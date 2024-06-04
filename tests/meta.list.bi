:i count 3
:b shell 26
./rere.py replay test.list
:i returncode 0
:b stdout 124
REPLAYING: echo 'Hello, World'
REPLAYING: echo 'Foo, bar'
REPLAYING: echo 'Ur, mom'
REPORT: 0 Skipped:
REPORT: 0 failed:
OK

:b stderr 0

:b shell 31
./rere.py replay skip-fail.list
:i returncode 1
:b stdout 448
REPLAYING: echo 'Hello, World'
UNEXPECTED: stdout
--- expected
+++ actual
@@ -1 +1 @@
-Hello, world
+Hello, World
REPLAYING: echo 'Foo, bar, baz'
NOT FOUND: shell command
    COMMAND:   echo 'Foo, bar, baz'
NOTE: You may want to do `./rere.py record skip-fail.list` to update skip-fail.list.bi
NOTE: Skiping this shell
REPLAYING: echo 'Ur, mom'
REPORT: 1 Skipped:
    SKIPPED: echo 'Foo, bar, baz'
REPORT: 1 failed:
    FAILED: echo 'Hello, World'

:b stderr 0

:b shell 26
./rere.py replay meta.list
:i returncode 0
:b stdout 160
REPLAYING: ./rere.py replay test.list
REPLAYING: ./rere.py replay skip-fail.list
REPLAYING: ./rere.py replay meta.list
REPORT: 0 Skipped:
REPORT: 0 failed:
OK


:b stderr 0

