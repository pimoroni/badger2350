import rp2
from badgeware import run
from machine import Timer

import binascii
import uctypes


# Get a CRC of the FAT (first 16k of the user filesystem) ~16ms
CACHE_FILE = "/.fsbackup"

fat = uctypes.bytearray_at(0x10300000, 16 * 1024)
crc = f"{binascii.crc32(fat):08x}"

try:
    cached_crc = open(f"{CACHE_FILE}.crc32", "r").read().strip()
except OSError:
    cached_crc = ""

if cached_crc != crc:
    with open(f"{CACHE_FILE}.crc32", "w") as f:
        f.write(crc)
        f.flush()
    with open(CACHE_FILE, "wb") as f:
        f.write(fat)
        f.flush()


rp2.enable_msc()

small_font = rom_font.winds
large_font = rom_font.nope

def activity_leds(_t):
    busy = rp2.is_msc_busy()
    badge.set_caselights(int(busy))


activity_timer = Timer()
activity_timer.init(period=100, callback=activity_leds)


class DiskMode():
    def __init__(self):
        self.transferring = False

    def draw(self):
        screen.pen = brush.pattern(color.white, color.dark_grey, 23)
        screen.clear()

        # draw the main window
        window = rect(10, 10, screen.width - 20, screen.height - 20)
        offset = 2

        screen.pen = color.dark_grey
        screen.shape(shape.rectangle(window.x + offset, window.y + offset,
                                     window.w + offset, window.h + offset))
        screen.pen = color.white
        screen.shape(shape.rectangle(window.x, window.y, window.w, window.h))
        screen.pen = color.black
        screen.shape(shape.rectangle(window.x, window.y, window.w, window.h).stroke(2))

        screen.pen = color.black
        screen.shape(shape.rectangle(window.x, window.y, window.w, 30).stroke(1))

        # draw the accent lines in the title bar of the window
        lines_y = window.y
        lines_y += 6
        for _ in range(5):
            lines_y += 3
            screen.line(vec2(window.x, lines_y), vec2(window.w + 10, lines_y))

        screen.font = large_font
        title = "USB Disk Mode"
        tw, _ = screen.measure_text(title)

        title_pos = vec2((window.x + window.w // 2) - (tw // 2), window.y + 9)
        screen.pen = color.white
        screen.rectangle(title_pos.x - 5, window.y + 2, tw + 10, 26)
        screen.pen = color.black
        screen.text(title, title_pos.x, title_pos.y)

        screen.pen = color.dark_grey
        text.draw(screen, "1: Your badge is now mounted as a disk", rect(30, 45, 210, 100))
        text.draw(screen, "2: Copy code onto it to experiment!", rect(30, 85, 210, 100))
        text.draw(screen, "3: Eject the disk to reboot your badge", rect(30, 125, 210, 100))


def center_text(text, y):
    w, h = screen.measure_text(text)
    screen.text(text, 80 - (w / 2), y)


disk_mode = DiskMode()


def update():
    # set transfer state here
    disk_mode.transferring = rp2.is_msc_busy()

    # draw the ui
    disk_mode.draw()


run(update)
