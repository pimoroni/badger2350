import binascii
import builtins
import gc
import json
import micropython
import os
import sys

import badgeware

ACK = "\x06"
CHUNK_SIZE = 4096


def _is_dir(path):
    try:
        return os.stat(path)[0] & 0x4000 != 0
    except OSError:
        return False


def _makedirs(path):
    current = ""
    for part in path.split("/"):
        if not part:
            continue
        current += "/" + part
        if not _is_dir(current):
            os.mkdir(current)


def _walk(path, entries):
    for name, kind, *_ in os.ilistdir(path):
        full = path.rstrip("/") + "/" + name
        if kind == 0x4000:
            entries.append([full, -1])
            _walk(full, entries)
        else:
            entries.append([full, os.stat(full)[6]])


def info():
    total, used, free = badge.disk_free("/")
    print(json.dumps({
        "version": sys.version,
        "implementation": os.uname().machine,
        "disk": [total, used, free],
        "mem_free": gc.mem_free(),
    }))


def ls(path="/"):
    entries = []
    if _is_dir(path):
        _walk(path, entries)
    print(json.dumps(entries))


def hashes(paths):
    import hashlib

    result = {}
    buf = bytearray(CHUNK_SIZE)
    for path in paths:
        try:
            digest = hashlib.sha256()
            with open(path, "rb") as f:
                while (count := f.readinto(buf)):
                    digest.update(memoryview(buf)[:count])
            result[path] = binascii.hexlify(digest.digest()).decode()
        except OSError:
            result[path] = None
    print(json.dumps(result))


def put(path, size):
    _makedirs(path.rsplit("/", 1)[0])
    buf = bytearray(CHUNK_SIZE)
    stdin = sys.stdin.buffer
    micropython.kbd_intr(-1)
    try:
        with open(path, "wb") as f:
            sys.stdout.write(ACK)
            remaining = size
            while remaining:
                view = memoryview(buf)[:min(CHUNK_SIZE, remaining)]
                received = 0
                while received < len(view):
                    received += stdin.readinto(view[received:])
                f.write(view)
                remaining -= len(view)
                sys.stdout.write(ACK)
    finally:
        micropython.kbd_intr(3)


def get(path):
    buf = bytearray(768)
    with open(path, "rb") as f:
        while (count := f.readinto(buf)):
            sys.stdout.write(binascii.b2a_base64(memoryview(buf)[:count]))


def rm(path):
    if _is_dir(path):
        for name, *_ in os.ilistdir(path):
            rm(path.rstrip("/") + "/" + name)
        os.rmdir(path)
    else:
        os.remove(path)


def mkdir(path):
    _makedirs(path)


def rename(source, destination):
    _makedirs(destination.rsplit("/", 1)[0])
    os.rename(source, destination)


def _run_file(path):
    with open(path, "r") as f:
        code = compile(f.read(), path, "exec")
    scope = {"__name__": "__main__", "__file__": path}
    try:
        exec(code, scope)
        update = scope.get("update")
        if callable(update):
            run(update)
    except Exception as e:  # noqa: BLE001
        fatal_error("Error!", e)


def execute(path, debug=False):
    builtins.ide_mode = True
    if debug:
        import ide_debug
        ide_debug.start()
    try:
        if _is_dir(path):
            launch(path)
        else:
            os.chdir(path.rsplit("/", 1)[0] or "/")
            _run_file(path)
    except badgeware.IDEStop:
        pass
    finally:
        if debug:
            ide_debug.stop()
        builtins.ide_mode = False
