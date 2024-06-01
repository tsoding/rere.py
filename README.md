# rere.py (**Re**cord **Re**play)

Universal Behavior Testing Tool in Python. The script is completely self-contained and expected to be simply copy-pasted to your project and modified as needed.

## Quick Start

1. Create a file with a shell command line per line. Let's call it `test.list`.
2. Record the expected behavior of each shell command:
```console
$ ./rere.py record test.list
```
The above command should create `test.list.bi` file with stdout, stderr, and returncode captured as the expected behavior. The file uses [bi format](https://github.com/tsoding/bi-format), for more infor see [Snapshot Schema](#snapshot-schema).

3. Replay the command lines checking their behavior against the recorded one:
```console
$ ./rere.py replay test.list.bi
```

4. `test.list.bi` is expected to be committed into the project repo.

## Snapshot Schema

The snapshot file uses [bi format](https://github.com/tsoding/bi-format). Its schema goes as following (the order of fields matters):

1. First comes an [Integer field][integer-field] `count` which denotes the amount of tests.
2. Then come the tests. Each test is a sequence of fields:
  1. [Blob field][blob-field] `shell` which contains the shell command to test,
  2. [Integer field][integer-field] `returncode` which contains the expected exit code of the shell command,
  3. [Blob field][blob-field] `stdout` which contains the bytes of the expected standard output,
  4. [Blob field][blob-field] `stderr` which contains the bytes of the expected standard error output.

See [test.list.bi](./test.list.bi) for an example.

[integer-field]: https://github.com/tsoding/bi-format/blob/5db184d9631cf2476a9fdf83b3daf1443eb6f18d/README.md#integer-field
[blob-field]: https://github.com/tsoding/bi-format/blob/5db184d9631cf2476a9fdf83b3daf1443eb6f18d/README.md#blob-field
