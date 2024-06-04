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

:b shell 37
./rere.py replay tests/skip-fail.list
:i returncode 1
:b stdout 460
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
NOTE: You may want to do `./rere.py record tests/skip-fail.list` to update tests/skip-fail.list.bi
NOTE: Skiping this shell
REPLAYING: echo 'Ur, mom'
REPORT: 1 Skipped:
    SKIPPED: echo 'Foo, bar, baz'
REPORT: 1 failed:
    FAILED: echo 'Hello, World'

:b stderr 0

:b shell 32
./rere.py replay tests/meta.list
:i returncode 0
:b stdout 171
REPLAYING: ./rere.py replay test.list
REPLAYING: ./rere.py replay tests/skip-fail.list
REPLAYING: ./rere.py replay tests/meta.list
REPORT: 0 Skipped:
REPORT: 0 failed:
OK

:b stderr 0

