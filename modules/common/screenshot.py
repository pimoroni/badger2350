"""Capture the display to a PNG or BMP file.

The source is any picovector image, defaulting to the global `screen`. Its buffer
is RGBA8888 (bytes R, G, B, A per pixel) and opaque, so a PNG RGBA scanline is the
raw row with a filter byte in front, no per-pixel reordering. BMP needs a per-pixel
BGR reorder, so it is the slower path.
"""

import io
import os
import struct
import binascii
import deflate


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _crc32(data):
    try:
        return binascii.crc32(data) & 0xFFFFFFFF
    except AttributeError:
        return _crc32_fallback(data)


# CRC32 table, built once on first use if binascii.crc32 is unavailable.
_crc_table = None


def _crc32_fallback(data):
    global _crc_table
    if _crc_table is None:
        _crc_table = []
        for n in range(256):
            c = n
            for _ in range(8):
                c = 0xEDB88320 ^ (c >> 1) if c & 1 else c >> 1
            _crc_table.append(c)
    crc = 0xFFFFFFFF
    for byte in data:
        crc = _crc_table[(crc ^ byte) & 0xFF] ^ (crc >> 8)
    return crc ^ 0xFFFFFFFF


def _png_chunk(file, tag, data):
    file.write(struct.pack(">I", len(data)))
    file.write(tag)
    file.write(data)
    file.write(struct.pack(">I", _crc32(tag + data)))


def _window_bits(row_bytes):
    """Smallest deflate window that spans a whole scanline.

    uzlib's LZ77 is a brute force search, so time is linear in window size, but
    rows repeat each other far more than they repeat themselves: a window one
    scanline deep is where the ratio arrives. Anything past it doubles the cost
    per step for a fraction of a percent.
    """
    bits = 8
    while (1 << bits) <= row_bytes and bits < 15:
        bits += 1
    return bits


def _write_png(file, raw, width, height, stride):
    file.write(PNG_SIGNATURE)
    _png_chunk(file, b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))

    row_bytes = width * 4
    filtered = io.BytesIO()
    stream = deflate.DeflateIO(filtered, deflate.ZLIB, _window_bits(row_bytes))
    if not hasattr(stream, "write"):
        raise RuntimeError("firmware built without MICROPY_PY_DEFLATE_COMPRESS")
    for y in range(height):
        start = y * stride
        stream.write(b"\x00")  # filter type: None
        stream.write(raw[start:start + row_bytes])
    stream.close()

    _png_chunk(file, b"IDAT", filtered.getvalue())
    _png_chunk(file, b"IEND", b"")


def _write_bmp(file, raw, width, height, stride):
    row_bytes = width * 3
    padding = (-row_bytes) & 3  # rows align to 4 bytes
    image_size = (row_bytes + padding) * height
    offset = 54  # file header (14) + info header (40)

    file.write(b"BM")
    file.write(struct.pack("<IHHI", offset + image_size, 0, 0, offset))
    file.write(struct.pack("<IiiHHIIiiII",
                           40, width, height, 1, 24, 0, image_size, 2835, 2835, 0, 0))

    pad = b"\x00" * padding
    for y in range(height - 1, -1, -1):  # BMP is bottom-up
        start = y * stride
        row = bytearray(row_bytes)
        src = start
        dst = 0
        while dst < row_bytes:
            row[dst] = raw[src + 2]      # B
            row[dst + 1] = raw[src + 1]  # G
            row[dst + 2] = raw[src]      # R
            src += 4
            dst += 3
        file.write(row)
        if padding:
            file.write(pad)


def _next_auto_path():
    try:
        os.mkdir("/screenshots")
    except OSError:
        pass
    existing = os.listdir("/screenshots")
    n = 0
    while "shot{:03d}.png".format(n) in existing:
        n += 1
    return "/screenshots/shot{:03d}.png".format(n)


def save(path=None, source=None):
    """Write `source` (default: the screen) to `path`.

    Format is chosen by extension: .png (default) or .bmp. With no path a new
    /screenshots/shotNNN.png is created. Returns the path written.
    """
    if source is None:
        source = screen
    if path is None:
        path = _next_auto_path()

    lower = path.lower()
    if lower.endswith(".png"):
        writer = _write_png
    elif lower.endswith(".bmp"):
        writer = _write_bmp
    else:
        raise ValueError("path must end in .png or .bmp")

    raw = source.raw
    width = source.width
    height = source.height
    stride = source.stride

    with open(path, "wb") as file:
        writer(file, raw, width, height, stride)

    return path
