:i count 3
:b shell 19
echo 'Hello, World'
:i returncode 0
:b stdout 13
Hello, World

:b stderr 0

:b shell 15
echo 'Foo, bar'
:i returncode 0
:b stdout 9
Foo, bar

:b stderr 0

:b shell 14
echo 'Ur, mom'
:i returncode 0
:b stdout 8
Ur, mom

:b stderr 0

