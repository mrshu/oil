#!/usr/bin/env bash
#
# Test combination of var ops.
#
# NOTE: There are also slice tests in {array,arith-context}.test.sh.

#### String slice
foo=abcdefg
echo ${foo:1:3}
## STDOUT:
bcd
## END

#### Cannot take length of substring slice
# These are runtime errors, but we could make them parse time errors.
v=abcde
echo ${#v:1:3}
## status: 1
## OK osh status: 2
# zsh actually implements this!
## OK zsh stdout: 3
## OK zsh status: 0

#### Out of range string slice: begin
# out of range begin doesn't raise error in bash, but in mksh it skips the
# whole thing!
foo=abcdefg
echo _${foo:100:3}
echo $?
## STDOUT:
_
0
## END
## BUG mksh stdout-json: "\n0\n"

#### Out of range string slice: length
# OK in both bash and mksh
foo=abcdefg
echo _${foo:3:100}
echo $?
## STDOUT:
_defg
0
## END
## BUG mksh stdout-json: "_defg\n0\n"

#### String slice: negative begin
foo=abcdefg
echo ${foo: -4:3}
## OK osh stdout:
## stdout: def

#### String slice: negative second arg is position, not length
foo=abcdefg
echo ${foo:3:-1} ${foo: 3: -2} ${foo:3 :-3 }
## OK osh stdout:
## stdout: def de d
## BUG mksh stdout: defg defg defg

#### strict-word-eval with string slice
set -o strict-word-eval || true
echo slice
s='abc'
echo -${s: -2}-
## STDOUT:
slice
## END
## status: 1
## N-I bash status: 0
## N-I bash STDOUT:
slice
-bc-
# END
## N-I mksh/zsh status: 1
## N-I mksh/zsh stdout-json: ""

#### String slice with math
# I think this is the $(()) language inside?
i=1
foo=abcdefg
echo ${foo: i+4-2 : i + 2}
## stdout: def

#### Slice undefined
echo -${undef:1:2}-
set -o nounset
echo -${undef:1:2}-
echo -done-
## STDOUT:
--
## END
## status: 1
# mksh doesn't respect nounset!
## BUG mksh status: 0
## BUG mksh STDOUT:
--
--
-done-
## END

#### Slice UTF-8 String
# mksh slices by bytes.
foo='--μ--'
echo ${foo:1:3}
## stdout: -μ-
## BUG mksh stdout: -μ

#### Slice string with invalid UTF-8 results in empty string and warning
s=$(echo -e "\xFF")bcdef
echo -${s:1:3}-
## status: 0
## STDOUT:
--
## END
## STDERR:
[??? no location ???] warning: Invalid start of UTF-8 character
## END
## BUG bash/mksh/zsh status: 0
## BUG bash/mksh/zsh STDOUT:
-bcd-
## END
## BUG bash/mksh/zsh stderr-json: ""


#### Slice string with invalid UTF-8 with strict-word-eval
set -o strict-word-eval || true
echo slice
s=$(echo -e "\xFF")bcdef
echo -${s:1:3}-
## status: 1
## stdout-json: "slice\n"
## N-I mksh/zsh status: 1
## N-I mksh/zsh stdout-json: ""
## N-I bash status: 0
## N-I bash stdout-json: "slice\n-bcd-\n"

#### Lower Case with , and ,,
x='ABC DEF'
echo ${x,}
echo ${x,,}
## STDOUT:
aBC DEF
abc def
## END
## N-I mksh/zsh stdout-json: ""
## N-I mksh/zsh status: 1


#### Upper Case with ^ and ^^
x='abc def'
echo ${x^}
echo ${x^^}
## STDOUT:
Abc def
ABC DEF
## END
## N-I mksh/zsh stdout-json: ""
## N-I mksh/zsh status: 1

#### Lower Case with constant string (VERY WEIRD)
x='AAA ABC DEF'
echo ${x,A}
echo ${x,,A}  # replaces every A only?
## STDOUT:
aAA ABC DEF
aaa aBC DEF
## END
## N-I mksh/zsh stdout-json: ""
## N-I mksh/zsh status: 1

#### Lower Case glob
x='ABC DEF'
echo ${x,[d-f]}
echo ${x,,[d-f]}  # This seems buggy, it doesn't include F?
## STDOUT:
ABC DEF
ABC deF
## END
## N-I mksh/zsh stdout-json: ""
## N-I mksh/zsh status: 1

#### ${x@Q}
x="FOO'BAR spam\"eggs"
eval "new=${x@Q}"
test "$x" = "$new" && echo OK
## STDOUT:
OK
## END
## N-I zsh stdout-json: ""
## N-I zsh status: 1

