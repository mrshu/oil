#!/usr/bin/env python2
"""
process_test.py: Tests for process.py
"""

import os
import unittest

from _devbuild.gen.id_kind_asdl import Id
from _devbuild.gen.runtime_asdl import redirect, arg_vector
from osh import builtin
from core import process  # module under test
from core import ui
from core import util
from core.util import log
from core import test_lib

Process = process.Process
ExternalThunk = process.ExternalThunk


def Banner(msg):
  print('-' * 60)
  print(msg)


_WAITER = process.Waiter()
_ARENA = test_lib.MakeArena('process_test.py')
_ERRFMT = ui.ErrorFormatter(_ARENA)
_FD_STATE = process.FdState(_ERRFMT)
_EXT_PROG = process.ExternalProgram(False, _FD_STATE, _ERRFMT,
                                    util.NullDebugFile())


def _CommandNode(code_str, arena):
  c_parser = test_lib.InitCommandParser(code_str, arena=arena)
  return c_parser.ParseLogicalLine()


def _ExtProc(argv):
  arg_vec = arg_vector(argv, [0] * len(argv))
  return Process(ExternalThunk(_EXT_PROG, arg_vec, {}))


class ProcessTest(unittest.TestCase):

  def testStdinRedirect(self):
    waiter = process.Waiter()
    fd_state = process.FdState(_ERRFMT)

    PATH = '_tmp/one-two.txt'
    # Write two lines
    with open(PATH, 'w') as f:
      f.write('one\ntwo\n')

    # Should get the first line twice, because Pop() closes it!

    r = redirect.PathRedirect(Id.Redir_Less, 0, PATH)
    fd_state.Push([r], waiter)
    line1 = builtin.ReadLineFromStdin()
    fd_state.Pop()

    fd_state.Push([r], waiter)
    line2 = builtin.ReadLineFromStdin()
    fd_state.Pop()

    # sys.stdin.readline() would erroneously return 'two' because of buffering.
    self.assertEqual('one\n', line1)
    self.assertEqual('one\n', line2)

  def testProcess(self):

    # 3 fds.  Does Python open it?  Shell seems to have it too.  Maybe it
    # inherits from the shell.
    print('FDS BEFORE', os.listdir('/dev/fd'))

    Banner('date')
    p = _ExtProc(['date'])
    status = p.Run(_WAITER)
    log('date returned %d', status)
    self.assertEqual(0, status)

    Banner('does-not-exist')
    p = _ExtProc(['does-not-exist'])
    print(p.Run(_WAITER))

    # 12 file descriptors open!
    print('FDS AFTER', os.listdir('/dev/fd'))

  def testPipeline(self):
    node = _CommandNode('uniq -c', _ARENA)
    ex = test_lib.InitExecutor(arena=_ARENA, ext_prog=_EXT_PROG)
    print('BEFORE', os.listdir('/dev/fd'))

    p = process.Pipeline()
    p.Add(_ExtProc(['ls']))
    p.Add(_ExtProc(['cut', '-d', '.', '-f', '2']))
    p.Add(_ExtProc(['sort']))

    p.AddLast((ex, node))

    pipe_status = p.Run(_WAITER, _FD_STATE)
    log('pipe_status: %s', pipe_status)

    print('AFTER', os.listdir('/dev/fd'))

  def testPipeline2(self):
    ex = test_lib.InitExecutor(arena=_ARENA, ext_prog=_EXT_PROG)

    Banner('ls | cut -d . -f 1 | head')
    p = process.Pipeline()
    p.Add(_ExtProc(['ls']))
    p.Add(_ExtProc(['cut', '-d', '.', '-f', '1']))

    node = _CommandNode('head', _ARENA)
    p.AddLast((ex, node))

    fd_state = process.FdState(_ERRFMT)
    print(p.Run(_WAITER, _FD_STATE))

    # Simulating subshell for each command
    node1 = _CommandNode('ls', _ARENA)
    node2 = _CommandNode('head', _ARENA)
    node3 = _CommandNode('sort --reverse', _ARENA)

    p = process.Pipeline()
    p.Add(Process(process.SubProgramThunk(ex, node1)))
    p.Add(Process(process.SubProgramThunk(ex, node2)))
    p.Add(Process(process.SubProgramThunk(ex, node3)))

    last_thunk = (ex, _CommandNode('cat', _ARENA))
    p.AddLast(last_thunk)

    print(p.Run(_WAITER, _FD_STATE))

    # TODO: Combine pipelines for other things:

    # echo foo 1>&2 | tee stdout.txt
    #
    # foo=$(ls | head)
    #
    # foo=$(<<EOF ls | head)
    # stdin
    # EOF
    #
    # ls | head &

    # Or technically we could fork the whole interpreter for foo|bar|baz and
    # capture stdout of that interpreter.

  def testOpen(self):
    fd_state = process.FdState(_ERRFMT)

    # This function used to raise BOTH OSError and IOError because Python 2 is
    # inconsistent.
    # We follow Python 3 in preferring OSError.
    # https://stackoverflow.com/questions/29347790/difference-between-ioerror-and-oserror
    self.assertRaises(OSError, fd_state.Open, '_nonexistent_')
    self.assertRaises(OSError, fd_state.Open, 'metrics/')


if __name__ == '__main__':
  unittest.main()
