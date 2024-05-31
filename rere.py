#!/usr/bin/env python3

import sys
import subprocess
from difflib import unified_diff
from typing import List, BinaryIO, Tuple, Optional

def read_blob_field(f: BinaryIO, name: bytes) -> bytes:
    line = f.readline()
    field = b':b ' + name + b' '
    assert line.startswith(field), "%s" % field
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
    print(f"Capturing `{shell}`...")
    process = subprocess.run(['sh', '-c', shell], capture_output = True)
    return {
        'shell': shell,
        'returncode': process.returncode,
        'stdout': process.stdout,
        'stderr': process.stderr,
    }

def dump_snapshots(file_path: str, snapshots: [dict]):
    with open(file_path, "wb") as f:
        write_int_field(f, b"count", len(snapshots))
        for snapshot in snapshots:
            write_blob_field(f, b"shell", bytes(snapshot['shell'], 'utf-8'))
            write_int_field(f, b"returncode", snapshot['returncode'])
            write_blob_field(f, b"stdout", snapshot['stdout'])
            write_blob_field(f, b"stderr", snapshot['stderr'])

def load_snapshots(file_path: str) -> [dict]:
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

        snapshots = []
        with open(test_list_path) as f:
            snapshots = [capture(shell.strip()) for shell in f]

        dump_snapshots(f'{test_list_path}.bi', snapshots)
    elif subcommand == 'replay':
        if len(argv) == 0:
            print(f'Usage: {program_name} {subcommand} <test.list>')
            print('ERROR: no test.list is provided')
            exit(1)
        test_list_path, *argv = argv

        snapshots = load_snapshots(f'{test_list_path}.bi')
        for snapshot in snapshots:
            print(f"Replaying `{snapshot['shell']}`...")
            process = subprocess.run(['sh', '-c', snapshot['shell']], capture_output = True);
            if process.returncode != snapshot['returncode']:
                print(f"UNEXPECTED RETURN CODE:")
                print(f"    EXPECTED: {snapshot['returncode']}")
                print(f"    ACTUAL:   {process.returncode}")
                exit(1)
            if process.stdout != snapshot['stdout']:
                a = snapshot['stdout'].decode('utf-8').splitlines(keepends=True)
                b = process.stdout.decode('utf-8').splitlines(keepends=True)
                print(f"UNEXPECTED STDOUT:")
                for line in unified_diff(a, b, fromfile="expected", tofile="actual"):
                    print(line, end='')
                exit(1)
            if process.stderr != snapshot['stderr']:
                a = snapshot['stderr'].decode('utf-8').splitlines(keepends=True)
                b = process.stderr.decode('utf-8').splitlines(keepends=True)
                print(f"UNEXPECTED STDERR:")
                for line in unified_diff(a, b, fromfile="expected", tofile="actual"):
                    print(line, end='')
                exit(1)
    else:
        print(f'ERROR: unknown subcommand {subcommand}');
        exit(1);
