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


ROMFS_HEADER = b"\xd2\xcd\x31"
ROMFS_PADDING = 1
ROMFS_DATA = 2
ROMFS_DIRECTORY = 4
ROMFS_FILE = 5
ROMFS_LENGTH_BYTES = 4


def _romfs_uint(value, width=0):
    out = [value & 0x7F]
    value >>= 7
    while value:
        out.insert(0, 0x80 | (value & 0x7F))
        value >>= 7
    while len(out) < width:
        out.insert(0, 0x80)
    return bytes(out)


def _romfs_record(kind, payload):
    return _romfs_uint(kind) + _romfs_uint(len(payload)) + payload


def _romfs_read_tree(path):
    entries = []
    for name, kind, *_ in os.ilistdir(path):
        full = path + "/" + name
        if kind == 0x4000:
            entries.append([name, _romfs_read_tree(full)])
        else:
            with open(full, "rb") as f:
                entries.append([name, f.read()])
    return entries


def _romfs_records(entries):
    out = bytearray()
    for name, entry in entries:
        encoded = name.encode()
        if isinstance(entry, list):
            out += _romfs_record(ROMFS_DIRECTORY, _romfs_uint(len(encoded)) + encoded + _romfs_records(entry))
        else:
            out += _romfs_record(ROMFS_FILE, _romfs_uint(len(encoded)) + encoded + _romfs_record(ROMFS_DATA, entry))
    return out


def _romfs_image(entries):
    data = _romfs_records(entries)
    if (len(ROMFS_HEADER) + ROMFS_LENGTH_BYTES + len(data)) % 2:
        data += _romfs_record(ROMFS_PADDING, b"\x00")
    return ROMFS_HEADER + _romfs_uint(len(data), ROMFS_LENGTH_BYTES) + data


def _romfs_device():
    import vfs
    return vfs.rom_ioctl(2, 0)


def _romfs_tree():
    try:
        return _romfs_read_tree("/rom")
    except OSError:
        return []


def _romfs_write(entries):
    import vfs
    image = _romfs_image(entries)
    device = _romfs_device()
    block_size = device.ioctl(5, 0)
    if len(image) > device.ioctl(4, 0) * block_size:
        raise OSError("ROM is full")
    current = memoryview(device)
    blocks = []
    buf = bytearray(block_size)
    for block in range((len(image) + block_size - 1) // block_size):
        chunk = image[block * block_size:(block + 1) * block_size]
        buf[:len(chunk)] = chunk
        buf[len(chunk):] = b"\xff" * (block_size - len(chunk))
        if bytes(current[block * block_size:(block + 1) * block_size]) != buf:
            blocks.append((block, bytes(buf)))
    try:
        vfs.umount("/rom")
    except OSError:
        pass
    for block, data in blocks:
        device.ioctl(6, block)
        device.writeblocks(block, data)
    vfs.mount(vfs.VfsRom(device), "/rom")
    return len(image), len(blocks)


def _romfs_place(entries, path, data):
    parts = path.strip("/").split("/")
    for part in parts[:-1]:
        for name, entry in entries:
            if name == part and isinstance(entry, list):
                entries = entry
                break
        else:
            sub = []
            entries.append([part, sub])
            entries = sub
    for index, (name, _) in enumerate(entries):
        if name == parts[-1]:
            if data is None:
                entries.pop(index)
            else:
                entries[index][1] = data
            return
    if data is not None:
        entries.append([parts[-1], data])


def rom_info():
    device = _romfs_device()
    total = device.ioctl(4, 0) * device.ioctl(5, 0)
    used = len(_romfs_image(_romfs_tree()))
    print(json.dumps({"total": total, "used": used}))


def rom_put(path, size):
    data = bytearray(size)
    view = memoryview(data)
    stdin = sys.stdin.buffer
    micropython.kbd_intr(-1)
    try:
        sys.stdout.write(ACK)
        for start in range(0, size, CHUNK_SIZE):
            end = min(start + CHUNK_SIZE, size)
            received = start
            while received < end:
                received += stdin.readinto(view[received:end])
            sys.stdout.write(ACK)
    finally:
        micropython.kbd_intr(3)
    tree = _romfs_tree()
    _romfs_place(tree, path, bytes(data))
    used, written = _romfs_write(tree)
    print(json.dumps({"used": used, "blocks": written}))


def rom_remove(path):
    tree = _romfs_tree()
    _romfs_place(tree, path, None)
    used, written = _romfs_write(tree)
    print(json.dumps({"used": used, "blocks": written}))


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
            os.chdir("/" if path.startswith("/.ide/") else path.rsplit("/", 1)[0] or "/")
            _run_file(path)
    except badgeware.IDEStop:
        pass
    finally:
        if debug:
            ide_debug.stop()
        builtins.ide_mode = False
