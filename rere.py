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

NAME_ENCODING = 'utf-8'
TEXT_ENCODING = 'utf-8'
IO_ENCODING = 'utf-8'

def bi_name(name : str) -> bytes:
    assert ' ' not in name
    return name.encode(NAME_ENCODING)

def read_blob_field(f: BinaryIO, name: str) -> bytes:
    line = f.readline()
    field = b':b ' + bi_name(name) + b' '
    assert line.startswith(field), field
    assert line.endswith(b'\n')
    size = int(line[len(field):-1])
    blob = f.read(size)
    assert f.read(1) == b'\n'
    return blob

def read_int_field(f: BinaryIO, name: str) -> int:
    line = f.readline()
    field = b':i ' + bi_name(name) + b' '
    assert line.startswith(field)
    assert line.endswith(b'\n')
    return int(line[len(field):-1])

def write_int_field(f: BinaryIO, name: str, value: int):
    f.write(b':i %s %d\n' % (bi_name(name), value))

def write_blob_field(f: BinaryIO, name: str, blob: bytes):
    f.write(b':b %s %d\n' % (bi_name(name), len(blob)))
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
        write_int_field(f, "count", len(snapshots))
        for snapshot in snapshots:
            write_blob_field(f, "shell", bytes(snapshot['shell'], TEXT_ENCODING))
            write_int_field(f, "returncode", snapshot['returncode'])
            write_blob_field(f, "stdout", snapshot['stdout'])
            write_blob_field(f, "stderr", snapshot['stderr'])

def load_snapshots(file_path: str) -> list[dict]:
    snapshots = []
    with open(file_path, "rb") as f:
        count = read_int_field(f, "count")
        for _ in range(count):
            shell = read_blob_field(f, "shell")
            returncode = read_int_field(f, "returncode")
            stdout = read_blob_field(f, "stdout")
            stderr = read_blob_field(f, "stderr")
            snapshot = {
                "shell": shell,
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr,
            }
            snapshots.append(snapshot)
    return snapshots

if __name__ == '__main__':
    program_name, *argv = sys.argv

    if len(argv) == 0:
        print(f'Usage: {program_name} <record|replay> <test.list>')
        print('ERROR: no subcommand is provided')
        exit(1)
    subcommand, *argv = argv

    if subcommand == 'record':
        if len(argv) == 0:
            print(f'Usage: {program_name} {subcommand} <test.list>')
            print('ERROR: no test.list is provided')
            exit(1)
        test_list_path, *argv = argv

        snapshots = [capture(shell.strip()) for shell in load_list(test_list_path)]
        dump_snapshots(f'{test_list_path}.bi', snapshots)
    elif subcommand == 'replay':
        if len(argv) == 0:
            print(f'Usage: {program_name} {subcommand} <test.list>')
            print('ERROR: no test.list is provided')
            exit(1)
        test_list_path, *argv = argv

        shells = load_list(test_list_path)
        snapshots = load_snapshots(f'{test_list_path}.bi')

        skipped_shells = []
        failed_shells = []

        snap_dict = {}
        for snapshot in snapshots:
            snapshot_shell = snapshot['shell'].decode(TEXT_ENCODING)
            snap_dict[snapshot_shell] = snapshot

        for shell in shells:
            print(f"REPLAYING: {shell}")
            if shell not in snap_dict:
                print(f"NOT FOUND: shell command")
                print(f"    COMMAND:   {shell}")
                print(f"NOTE: You may want to do `{program_name} record {test_list_path}` to update {test_list_path}.bi")
                print(f"NOTE: Skiping this shell")
                skipped_shells.append(shell)
                continue

            snapshot = snap_dict[shell]

            process = subprocess.run(['sh', '-c', shell], capture_output = True);
            failed = False
            if process.returncode != snapshot['returncode']:
                print(f"UNEXPECTED: return code")
                print(f"    EXPECTED: {snapshot['returncode']}")
                print(f"    ACTUAL:   {process.returncode}")
                failed = True
            if process.stdout != snapshot['stdout']:
                # TODO: support binary outputs
                a = snapshot['stdout'].decode(IO_ENCODING).splitlines(keepends=True)
                b = process.stdout.decode(IO_ENCODING).splitlines(keepends=True)
                print(f"UNEXPECTED: stdout")
                for line in unified_diff(a, b, fromfile="expected", tofile="actual"):
                    print(line, end='')
                failed = True
            if process.stderr != snapshot['stderr']:
                a = snapshot['stderr'].decode(IO_ENCODING).splitlines(keepends=True)
                b = process.stderr.decode(IO_ENCODING).splitlines(keepends=True)
                print(f"UNEXPECTED: stderr")
                for line in unified_diff(a, b, fromfile="expected", tofile="actual"):
                    print(line, end='')
                failed = True
            if failed:
                failed_shells.append(shell)

        print(f'REPORT: {len(skipped_shells)} Skipped:')
        for skipped in skipped_shells:
            print(f'    SKIPPED: {skipped}')

        print(f'REPORT: {len(failed_shells)} failed:')
        for failed in failed_shells:
            print(f'    FAILED: {failed}')

        if len(skipped_shells) == 0 and len(failed_shells) == 0:
            print('OK')
        else:
            exit(1)
    else:
        print(f'ERROR: unknown subcommand {subcommand}');
        exit(1);
