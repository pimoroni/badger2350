import gc
from io import StringIO
import sys
import time

import machine
import ssd1680
import builtins

import picovector


SLEEP_TIMEOUT_MS = 5000


def set_brightness(value):
    pass


def run(update, init=None, on_exit=None):
    screen.font = DEFAULT_FONT
    screen.pen = color.white
    screen.clear()
    screen.pen = badge.default_pen()
    first_refresh = True

    try:
        if init:
            init()
        try:
            badge.poll()
            while True:
                if badge.default_clear() is not None:
                    screen.pen = badge.default_clear()
                    screen.clear()
                screen.pen = badge.default_pen()
                if (result := update()) is not None:
                    return result
                gc.collect()

                # Perform the dither on the screen raw buffer
                if badge.mode() & DITHER:
                    screen.dither()

                if first_refresh:
                    display.speed(0)

                display.update()

                if first_refresh:
                    display.speed((badge.mode() >> 4) & 0xf)
                    first_refresh = False

                # Wait for input or sleep
                t_start = time.ticks_ms()
                while True:
                    badge.poll()
                    if badge.pressed():
                        break
                    if rtc.alarm_status():
                        rtc.clear_alarm()
                        break
                    # put the unit to sleep if button input times out and the unit is not connected via USB
                    if time.ticks_diff(time.ticks_ms(), t_start) > SLEEP_TIMEOUT_MS and not badge.usb_connected():
                        badge.sleep()
        finally:
            if on_exit:
                on_exit()

    except Exception as e:  # noqa: BLE001
        fatal_error("Error!", get_exception(e))


def get_exception(e):
    s = StringIO()
    sys.print_exception(e, s)
    s.seek(0)
    s.readline()  # Drop the "Traceback" bit
    return s.read()


# Draw an overlay box with a given message within it
def message(title, msg, window=None):
    error_window = window or screen.window(0, 0, screen.width, screen.height)
    error_window.font = DEFAULT_FONT

    error_window.pen = brush.pattern(color.white, color.dark_grey, 23)
    error_window.clear()

    # draw the main window
    window = rect(10, 10, error_window.width - 20, error_window.height - 20)
    offset = 2

    error_window.pen = color.dark_grey
    error_window.shape(shape.rectangle(window.x + offset, window.y + offset,
                                       window.w + offset, window.h + offset))
    error_window.pen = color.white
    error_window.shape(shape.rectangle(window.x, window.y, window.w, window.h))
    error_window.pen = color.black
    error_window.shape(shape.rectangle(window.x, window.y, window.w, window.h).stroke(2))

    error_window.pen = color.black
    error_window.shape(shape.rectangle(window.x, window.y, window.w, 30).stroke(1))

    # draw the accent lines in the title bar of the window
    lines_y = window.y
    lines_y += 6
    for _ in range(5):
        lines_y += 3
        error_window.line(vec2(window.x, lines_y), vec2(window.w + 10, lines_y))

    error_window.font = rom_font.nope
    tw, _ = error_window.measure_text(title)

    title_pos = vec2((window.x + window.w // 2) - (tw // 2), window.y + 9)
    error_window.pen = color.white
    error_window.rectangle(title_pos.x - 5, window.y + 2, tw + 10, 26)
    error_window.pen = color.black
    error_window.text(title, title_pos.x, title_pos.y)

    error_window.pen = color.black
    error_window.font = rom_font.winds
    bounds = error_window.clip
    bounds.y += 43
    bounds.x += 18
    bounds.w -= 30
    bounds.h -= 35

    error_window.pen = color.dark_grey
    error_window.shape(shape.rectangle((window.w - 45) + offset, (window.h - 15) + offset, 33, 15))

    error_window.pen = color.white
    error_window.shape(shape.rectangle(window.w - 45, window.h - 15, 33, 15))

    error_window.pen = color.black
    error_window.shape(shape.rectangle(window.w - 45, window.h - 15, 33, 15).stroke(1))

    error_window.text("Okay", vec2(window.w - 39, window.h - 14))

    text.draw(error_window, msg, bounds=bounds)


def fatal_error(title, error):
    if not isinstance(error, str):
        error = get_exception(error)
    print(f"- ERROR: {error}")

    message(title, error)

    display.update()
    while True:
        badge.poll()
        if badge.pressed():
            break
    while badge.pressed():
        badge.poll()

    State.delete("menu")

    machine.reset()


display = ssd1680.SSD1680()

# Import PicoSystem module constants to builtins,
# so they are available globally.
for k, v in picovector.__dict__.items():
    if not k.startswith("__"):
        setattr(builtins, k, v)

# Hoist image anti-aliasing constants
builtins.OFF = image.OFF
builtins.X2 = image.X2
builtins.X4 = image.X4

# Hoist display and run for clean Thonny apps
builtins.display = display
builtins.run = run
builtins.fatal_error = fatal_error

# Import badgeware modules
__import__(".frozen/badgeware/badge")
__import__(".frozen/badgeware/math")
__import__(".frozen/badgeware/text")
__import__(".frozen/badgeware/sprite")
__import__(".frozen/badgeware/filesystem")
__import__(".frozen/badgeware/memory")
__import__(".frozen/badgeware/rtc")
State = __import__(".frozen/badgeware/state").State

DEFAULT_FONT = rom_font.sins

badge.mode(LORES | VSYNC)
badge.default_pen(color.black)
badge.default_clear(color.white)
