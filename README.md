# rere.py (**Re**cord **Re**play)

Universal Behavior Testing Tool in Python.

## Quick Start

1. Create a file with a shell command line per line. Let's call it `test.list`.
2. Record the expected behavior of each shell command:
```console
$ ./rere.py record test.list
```
The above command should create `test.list.bi` file with stdout, stderr, and returncode captured as the expected behavior.
3. Replay the command lines checking their behavior against the recorded one:
```console
$ ./rere.py replay test.list.bi
```
