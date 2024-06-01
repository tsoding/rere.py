#!/usr/bin/env python3
# Copyright 2024 Alexey Kutepov <reximkut@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sys
import subprocess
from difflib import unified_diff
from typing import List, BinaryIO, Tuple, Optional

def read_blob_field(f: BinaryIO, name: bytes) -> bytes:
    line = f.readline()
    field = b':b ' + name + b' '
    assert line.startswith(field), field
    assert line.endswith(b'\n')
    size = int(line[len(field):-1])
    blob = f.read(size)
    assert f.read(1) == b'\n'
    return blob

def read_int_field(f: BinaryIO, name: bytes) -> int:
    line = f.readline()
    field = b':i ' + name + b' '
    assert line.startswith(field)
    assert line.endswith(b'\n')
    return int(line[len(field):-1])

def write_int_field(f: BinaryIO, name: bytes, value: int):
    f.write(b':i %s %d\n' % (name, value))

def write_blob_field(f: BinaryIO, name: bytes, blob: bytes):
    f.write(b':b %s %d\n' % (name, len(blob)))
    f.write(blob)
    f.write(b'\n')

def capture(shell: str) -> dict:
    print(f"CAPTURING: {shell}")
    process = subprocess.run(['sh', '-c', shell], capture_output = True)
    return {
        'shell': shell,
        'returncode': process.returncode,
        'stdout': process.stdout,
        'stderr': process.stderr,
    }

def load_list(file_path: str) -> list[str]:
    with open(file_path) as f:
        return [line.strip() for line in f]

def dump_snapshots(file_path: str, snapshots: list[dict]):
    with open(file_path, "wb") as f:
        write_int_field(f, b"count", len(snapshots))
        for snapshot in snapshots:
            write_blob_field(f, b"shell", bytes(snapshot['shell'], 'utf-8'))
            write_int_field(f, b"returncode", snapshot['returncode'])
            write_blob_field(f, b"stdout", snapshot['stdout'])
            write_blob_field(f, b"stderr", snapshot['stderr'])

def load_snapshots(file_path: str) -> list[dict]:
    snapshots = []
    with open(file_path, "rb") as f:
        count = read_int_field(f, b"count")
        for _ in range(count):
            shell = read_blob_field(f, b"shell")
            returncode = read_int_field(f, b"returncode")
            stdout = read_blob_field(f, b"stdout")
            stderr = read_blob_field(f, b"stderr")
            snapshot = {
                "shell": shell,
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr,
            }
            snapshots.append(snapshot)
    return snapshots

match __name__:
    case '__main__':
        program_name, *argv = sys.argv

        match len(argv):
            case 0:
                print(f'Usage: {program_name} <record|replay> <test.list>')
                print('ERROR: no subcommand is provided')
                exit(1)
        subcommand, *argv = argv

        if subcommand == 'record':
            match len(argv):
                case 0:
                    print(f'Usage: {program_name} {subcommand} <test.list>')
                    print('ERROR: no test.list is provided')
                    exit(1)
            test_list_path, *argv = argv

            snapshots = [capture(shell.strip()) for shell in load_list(test_list_path)]
            dump_snapshots(f'{test_list_path}.bi', snapshots)
        elif subcommand == 'replay':
            match len(argv):
                case 0:
                    print(f'Usage: {program_name} {subcommand} <test.list>')
                    print('ERROR: no test.list is provided')
                    exit(1)
            test_list_path, *argv = argv

            shells = load_list(test_list_path)
            snapshots = load_snapshots(f'{test_list_path}.bi')

            match len(shells) != len(snapshots):
                case True:
                    print(f"UNEXPECTED: Amount of shell commands in f{test_list_path}")
                    print(f"    EXPECTED: {len(snapshots)}")
                    print(f"    ACTUAL:   {len(shells)}")
                    print(f"NOTE: You may want to do `{program_name} record {test_list_path}` to update {test_list_path}.bi")
                    exit(1)

            for (shell, snapshot) in zip(shells, snapshots):
                print(f"REPLAYING: {shell}")
                snapshot_shell = snapshot['shell'].decode('utf-8')
                match shell != snapshot_shell:
                    case True:
                        print(f"UNEXPECTED: shell command")
                        print(f"    EXPECTED: {snapshot_shell}")
                        print(f"    ACTUAL:   {shell}")
                        print(f"NOTE: You may want to do `{program_name} record {test_list_path}` to update {test_list_path}.bi")
                        exit(1)
                process = subprocess.run(['sh', '-c', shell], capture_output = True);
                match process.returncode != snapshot['returncode']:
                    case True:
                        print(f"UNEXPECTED: return code")
                        print(f"    EXPECTED: {snapshot['returncode']}")
                        print(f"    ACTUAL:   {process.returncode}")
                        exit(1)
                match process.stdout != snapshot['stdout']:
                    case True:
                        # TODO: support binary outputs
                        a = snapshot['stdout'].decode('utf-8').splitlines(keepends=True)
                        b = process.stdout.decode('utf-8').splitlines(keepends=True)
                        print(f"UNEXPECTED: stdout")
                        for line in unified_diff(a, b, fromfile="expected", tofile="actual"):
                            print(line, end='')
                        exit(1)
                match process.stderr != snapshot['stderr']:
                    case True:
                        a = snapshot['stderr'].decode('utf-8').splitlines(keepends=True)
                        b = process.stderr.decode('utf-8').splitlines(keepends=True)
                        print(f"UNEXPECTED: stderr")
                        for line in unified_diff(a, b, fromfile="expected", tofile="actual"):
                            print(line, end='')
                        exit(1)
            print('OK')
        else:
            print(f'ERROR: unknown subcommand {subcommand}');
            exit(1);
