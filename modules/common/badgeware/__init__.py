import gc
from io import StringIO
import sys
import time
import os

import machine
import ssd1680
import builtins

import picovector


def set_brightness(value):
    pass


def reset():
    # HOME is also BOOT; if we reset while it's
    # low we'll end up in bootloader mode.
    badge.poll()
    while badge.pressed() or badge.held():
        badge.poll()
    machine.reset()


class _run:
    @property
    def ticks(self):
        return badge.ticks - self.start

    @property
    def progress(self):
        return 0 if self.duration is None else self.ticks / self.duration

    def __init__(self, *args, duration=None):
        self.start = 0
        self.result = None
        self.duration = duration
        if len(args) == 1 and callable(args[0]):
            self(args[0])

    def __call__(self, update):
        badge.poll()
        self.start = badge.ticks
        parent = loop
        builtins.loop = self

        try:
            while True:
                if (result := update()) is not None:
                    self.result = result
                    return

                if self.duration is not None and self.ticks >= self.duration:
                    return

        finally:
            builtins.loop = parent


def wait_for_button_or_alarm(timeout=30_000):
    # Wait for input or sleep
    t_start = time.ticks_ms()
    while True:
        badge.poll()
        if badge.pressed():
            break
        if rtc.alarm_status():
            break
        # put the unit to sleep if button input times out and the unit is not connected via USB
        if timeout is not None and time.ticks_diff(time.ticks_ms(), t_start) > timeout and not badge.usb_connected():
            badge.sleep()


def clear_running():
    state = {
        "active": 0,
        "running": "/system/apps/menu"
    }
    State.load("menu", state)
    state["running"] = "/system/apps/menu"
    State.modify("menu", state)
    rtc.clear_alarm()


def launch(path):
    badge.first_update = True

    def do_exit():
        if path in sys.modules:
            app = sys.modules[path]
            on_exit = getattr(app, "on_exit", None)
            return on_exit() if callable(on_exit) else on_exit
        return None

    def quit_to_launcher(_pin):
        do_exit()
        clear_running()
        reset()

    machine.Pin.board.BUTTON_HOME.irq(
        trigger=machine.Pin.IRQ_FALLING, handler=quit_to_launcher
    )

    # Grab a list of modules from before launching app
    modules_before_launch = list(sys.modules.keys())

    try:
        os.chdir(path)
        sys.path.insert(0, path)
        __import__(path)  # App may block here

        return do_exit()

    except Exception as e:  # noqa: BLE001
        fatal_error("Error!", get_exception(e))

    finally:
        # Clean up path
        if sys.path[0].startswith("/system/apps"):
            sys.path.pop(0)

        # Clean up any imported modules
        for key in sys.modules.keys():
            if key not in modules_before_launch:
                del sys.modules[key]

        gc.collect()


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
builtins.run = _run
builtins.launch = launch
builtins.loop = None
builtins.reset = reset
builtins.wait_for_button_or_alarm = wait_for_button_or_alarm
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
badge.default_pen = color.black
badge.default_clear = color.white
