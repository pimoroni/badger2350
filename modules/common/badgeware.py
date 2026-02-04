import gc
import json
import os
import io as stream
import sys
import time
import random
import pcf85063a

import machine
import powman
import ssd1680
import builtins

import board

import picovector

display = ssd1680.SSD1680()

SLEEP_TIMEOUT_MS = 5000

_CASE_LIGHTS = [machine.PWM(machine.Pin.board.CL0), machine.PWM(machine.Pin.board.CL1),
                machine.PWM(machine.Pin.board.CL2), machine.PWM(machine.Pin.board.CL3)]

for led in _CASE_LIGHTS:
    led.freq(500)


def set_case_led(led, value):
    if not isinstance(led, int):
        raise TypeError("LED must be a number between 0 and 3")

    if led < 0 or led > len(_CASE_LIGHTS) - 1:
        raise ValueError("LED out of range!")

    if not isinstance(value, (int, float)):
        raise TypeError("brightness must be a number between 0.0 and 1.0")

    if value < 0 or value > 1.0:
        raise ValueError("brightness must be between 0.0 and 1.0")

    value = int(value * 65535)
    _CASE_LIGHTS[led].duty_u16(value)


def get_case_led(led=None):

    if led is None:
        raise ValueError("LED must be provided!")

    if not isinstance(led, int):
        raise TypeError("LED must be a number between 0 and 3")

    if led < 0 or led > len(_CASE_LIGHTS) - 1:
        raise ValueError("LED out of range!")

    return _CASE_LIGHTS[led].duty_u16() / 65535


def get_light():
    # TODO: Not supported
    return 0


def localtime_to_rtc():
    rtc.datetime(time.localtime())


def rtc_to_localtime():
    dt = rtc.datetime()
    machine.RTC().datetime((dt[0], dt[1], dt[2], dt[6], dt[3], dt[4], dt[5], 0))


def time_from_ntp():
    import ntptime

    ntptime.settime()
    del sys.modules["ntptime"]
    gc.collect()
    localtime_to_rtc()


def pen_glyph_renderer(_image, parameters, _cursor, measure):
    if measure:
        return 0
    pen(*(int(c) for c in parameters))
    return None


def text_tokenise(image, text, glyph_renderers=None, size=24):
    WORD = 1
    SPACE = 2
    LINE_BREAK = 3

    default_glyph_renderers = {"pen": pen_glyph_renderer}
    default_glyph_renderers.update(glyph_renderers or {})

    tokens = []

    for line in text.splitlines():
        start, end = 0, 0
        i = 0
        while end < len(line):
            # check for a glyph_renderer
            if default_glyph_renderers and line.find("[", start) == start:
                glyph_end = line.find("]", start)
                # look ahead to see if this is an escape code
                glyph_renderer = line[start + 1:glyph_end]
                parameters = []
                if ":" in glyph_renderer:
                    code, parameters = glyph_renderer.split(":")
                    parameters = parameters.split(",")
                else:
                    code = glyph_renderer

                if code in default_glyph_renderers:
                    w = default_glyph_renderers[code](None, parameters, None, True)
                    tokens.append((default_glyph_renderers[code], w, tuple(parameters)))
                    start = glyph_end + 1
                    continue

            i += 1

            # search for the next space or glyph
            next_space = line.find(" ", start)
            next_glyph = line.find("[", start + 1)

            end = min(next_space, next_glyph)
            if end == -1:
                end = max(next_space, next_glyph)
            if end == -1:
                end = len(line)

            # measure the text up to the space
            if end > start:
                if isinstance(image.font, font):
                    width, _ = image.measure_text(line[start:end], size)
                else:
                    width, _ = image.measure_text(line[start:end])
                tokens.append((WORD, width, line[start:end]))

            start = end
            if end < len(line) and line[end] == " ":
                tokens.append((SPACE,))
                start += 1

        tokens.append((LINE_BREAK,))

    return tokens


def text_draw(image, text, bounds=None, line_spacing=1, word_spacing=1, size=24):
    WORD = 1
    SPACE = 2
    LINE_BREAK = 3

    if bounds is None:
        bounds = rect(0, 0, image.width, image.height)
    else:
        bounds = rect(int(bounds.x), int(bounds.y), int(bounds.w), int(bounds.h))

    if isinstance(text, str):
        tokens = text_tokenise(image, text, size=size)
    else:
        tokens = text

    old_clip = image.clip
    image.clip = bounds

    c = vec2(bounds.x, bounds.y)
    b = rect()
    for token in tokens:
        font_height = size if isinstance(image.font, font) else image.font.height
        if token[0] == WORD:
            if c.x + token[1] > bounds.x + bounds.w:
                c.x = bounds.x
                c.y += font_height * line_spacing
            if isinstance(image.font, font):
                image.text(token[2], c.x, c.y, size)
            else:
                image.text(token[2], c.x, c.y)
            c.x += token[1]
        elif token[0] == SPACE:
            c.x += (font_height / 3) * word_spacing
        elif token[0] == LINE_BREAK:
            c.x = bounds.x
            c.y += font_height * line_spacing
        else:
            if c.x + token[1] > bounds.x + bounds.w:
                c.x = bounds.x
                c.y += font_height * line_spacing

            token[0](image, token[2], c, False)
            c.x += token[1]

        b.w = max(b.w, c.x)
        b.h = max(b.h, c.y)

    image.clip = old_clip
    return b


def clamp(v, vmin, vmax):
    return max(vmin, min(v, vmax))


def rnd(v1, v2=None):
    if v2:
        return random.randint(v1, v2)
    return random.randint(0, v1)


def frnd(v1, v2=None):
    if v2:
        return random.uniform(v1, v2)
    return random.uniform(0, v1)


def file_exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def is_dir(path):
    try:
        flags = os.stat(path)
        return flags[0] & 0x4000  # is a directory
    except:  # noqa: E722
        return False


class SpriteSheet:
    def __init__(self, file, columns, rows):
        self.image = image.load(file)
        self.sw = int(self.image.width / columns)
        self.sh = int(self.image.height / rows)

        self.sprites = []
        for x in range(columns):
            column = []
            for y in range(rows):
                sprite = self.image.window(self.sw * x, self.sh * y, self.sw, self.sh)
                column.append(sprite)
            self.sprites.append(column)

    def sprite(self, x, y):
        return self.sprites[x][y]

    def animation(self, x=0, y=0, count=None, horizontal=True):
        if not count:
            count = int(self.image.width / self.sw)
        return AnimatedSprite(self, x, y, count, horizontal)


class AnimatedSprite:
    def __init__(self, spritesheet, x, y, count, horizontal=True):
        self.spritesheet = spritesheet
        self.frames = []
        for _ in range(count):
            self.frames.append((x, y))
            if horizontal:
                x += 1
            else:
                y += 1

    def frame(self, frame_index=0):
        frame_index = int(frame_index)
        frame_index %= len(self.frames)
        return self.spritesheet.sprite(
            self.frames[frame_index][0], self.frames[frame_index][1]
        )

    def count(self):
        return len(self.frames)


class State:
    @staticmethod
    def delete(app):
        try:
            os.remove("/state/{}.json".format(app))
        except OSError:
            pass

    @staticmethod
    def save(app, data):
        try:
            with open("/state/{}.json".format(app), "w") as f:
                f.write(json.dumps(data))
                f.flush()
        except OSError:
            import os

            try:
                os.stat("/state")
            except OSError:
                os.mkdir("/state")
                State.save(app, data)

    @staticmethod
    def modify(app, data):
        state = {}
        State.load(app, state)
        state.update(data)
        State.save(app, state)

    @staticmethod
    def load(app, defaults):
        try:
            data = json.loads(open("/state/{}.json".format(app), "r").read())
            if type(data) is dict:
                defaults.update(data)
                return True
        except (OSError, ValueError):
            pass

        State.save(app, defaults)
        return False


# show the current free memory including the delta since last time the
# function was called, optionally include a custom message
_lf = None


def free(message=""):
    global _lf
    import gc

    gc.collect()  # collect any free memory before reporting
    f = int(gc.mem_free() / 1024)
    print(f"{message}: {f}kb", end="")
    if _lf:
        delta = f - _lf
        sign = "-" if delta < 0 else "+"
        print(f" ({sign}{abs(delta)}kb)", end="")
    print("")
    _lf = f


def woken_by_button():
    return powman.get_wake_reason() in (
        powman.WAKE_BUTTON_A,
        powman.WAKE_BUTTON_B,
        powman.WAKE_BUTTON_C,
        powman.WAKE_BUTTON_UP,
        powman.WAKE_BUTTON_DOWN,
    )


def pressed_to_wake(button):
    # TODO: BUTTON_HOME cannot be a wake button
    # so maybe raise an exception
    return button in powman.get_wake_buttons()


def woken_by_reset():
    return powman.get_wake_reason() == 255


def sleep():
    powman.sleep()


class Assets:
    @staticmethod
    def font(name):
        file = f"{ASSETS}/fonts/{name}.ppf"
        try:
            return pixel_font.load(file)
        except OSError as e:
            raise ValueError(f'Font "{name}" not found. (Missing {file}?)') from e

    @staticmethod
    def fonts():
        return [f[:-4] for f in os.listdir(f"{ASSETS}/fonts") if f.endswith(".ppf")]


def is_charging():
    # We only want to return the charge status if the USB cable is connected.
    if VBUS_DETECT.value():
        return not CHARGE_STAT.value()

    return False


def get_usb_connected():
    return bool(VBUS_DETECT.value())


def sample_adc_u16(adc, samples=1):
    val = []
    for _ in range(samples):
        val.append(adc.read_u16())
    return sum(val) / len(val)


def get_battery_level():
    # Use the battery voltage to estimate the remaining percentage

    # Get the average reading over 20 samples from our VBAT and VREF
    voltage = sample_adc_u16(VBAT_SENSE, 10) * conversion_factor * 2
    vref = sample_adc_u16(SENSE_1V1, 10) * conversion_factor
    voltage = voltage / vref * 1.1

    # Return the battery level as a percentage
    return min(100, max(0, round(123 - (123 / pow((1 + pow((voltage / 3.2), 80)), 0.165)))))


def get_disk_usage(mountpoint="/"):
    # f_bfree and f_bavail should be the same?
    # f_files, f_ffree, f_favail and f_flag are unsupported.
    f_bsize, f_frsize, f_blocks, f_bfree, _, _, _, _, _, f_namemax = os.statvfs(
        mountpoint
    )

    f_total_size = f_frsize * f_blocks
    f_total_free = f_bsize * f_bfree
    f_total_used = f_total_size - f_total_free

    f_used = 100 / f_total_size * f_total_used
    f_free = 100 / f_total_size * f_total_free

    return f_total_size, f_used, f_free


def mode(mode, force=False):
    global _current_mode

    if mode == _current_mode and not force:
        return False

    _current_mode = mode

    # Set display update speed
    display.speed((_current_mode >> 4) & 0xf)

    return True


def run(update, init=None, on_exit=None, auto_clear=True):
    screen.font = DEFAULT_FONT
    screen.pen = BG
    screen.clear()
    screen.pen = FG
    first_refresh = True

    try:
        if init:
            init()
        try:
            io.poll()
            while True:
                if auto_clear:
                    screen.pen = BG
                    screen.clear()
                    screen.pen = FG
                if (result := update()) is not None:
                    return result
                gc.collect()

                # Perform the dither on the screen raw buffer
                if _current_mode & DITHER:
                    screen.dither()

                if first_refresh:
                    display.speed(0)

                display.update()

                if first_refresh:
                    display.speed((_current_mode >> 4) & 0xf)
                    first_refresh = False

                # Wait for input or sleep
                t_start = time.ticks_ms()
                while True:
                    io.poll()
                    if io.pressed:
                        break
                    if board.RTC_ALARM.value() == 0:
                        rtc.clear_alarm_flag()
                        rtc.clear_timer_flag()
                        break
                    # put the unit to sleep if button input times out and the unit is not connected via USB
                    if time.ticks_diff(time.ticks_ms(), t_start) > SLEEP_TIMEOUT_MS and not VBUS_DETECT.value():
                        powman.sleep()
        finally:
            if on_exit:
                on_exit()

    except Exception as e:  # noqa: BLE001
        fatal_error("Error!", get_exception(e))


def get_exception(e):
    s = stream.StringIO()
    sys.print_exception(e, s)
    s.seek(0)
    s.readline()  # Drop the "Traceback" bit
    return s.read()


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

    text_draw(error_window, msg, bounds=bounds)


def fatal_error(title, error):
    if not isinstance(error, str):
        error = get_exception(error)
    print(f"- ERROR: {error}")

    if _current_mode == LORES:
        contents = image(160, 120)
        contents.blit(screen, vec2(0, 0))
        mode(HIRES)
        screen.blit(contents, rect(0, 0, 320, 240))
        del contents

    message(title, error)

    display.update()
    while True:
        io.poll()
        if io.pressed:
            break
    while io.pressed:
        io.poll()

    State.delete("menu")

    machine.reset()


def load_font(font_file):
    search_paths = ("/rom/fonts", "/system/assets/fonts", "/fonts", "/assets", "")
    file = font_file

    # Remove /rom/fonts if searching for .af files
    if file.endswith(".af"):
        search_paths = search_paths[1:]

    extensions = (".af", ".ppf") if not file.endswith(".af") and not file.endswith(".ppf") else ("", )

    for search_path in search_paths:
        for ext in extensions:
            path = search_path + f"/{file}{ext}"
            if file_exists(path) and not is_dir(path):
                return font.load(path) if path.endswith(".af") else pixel_font.load(path)

    raise OSError(f'Font "{font_file}" not found!')


class ROMFonts:
    def __getattr__(self, key):
        try:
            return pixel_font.load(f"/rom/fonts/{key}.ppf")
        except OSError as e:
            raise AttributeError(f"Font {key} not found!") from e

    def __dir__(self):
        return [f[:-4] for f in os.listdir("/rom/fonts") if f.endswith(".ppf")]


rom_font = ROMFonts()

# RTC
rtc = pcf85063a.PCF85063A(machine.I2C())

if time.localtime()[0] >= 2025:
    localtime_to_rtc()

elif rtc.datetime()[0] >= 2025:
    rtc_to_localtime()


# Import PicoSystem module constants to builtins,
# so they are available globally.
for k, v in picovector.__dict__.items():
    if not k.startswith("__"):
        setattr(builtins, k, v)


ASSETS = "/system/assets"
DEFAULT_FONT = rom_font.sins
ERROR_FONT = rom_font.desert

FG = color.black
BG = color.white

VBAT_SENSE = machine.ADC(machine.Pin.board.VBAT_SENSE)
VBUS_DETECT = machine.Pin.board.VBUS_DETECT
CHARGE_STAT = machine.Pin.board.CHARGE_STAT
SENSE_1V1 = machine.ADC(machine.Pin.board.SENSE_1V1)

BAT_MAX = 4.10
BAT_MIN = 3.00

HIRES = 1
LORES = 0
FAST_UPDATE = 3 << 4
FULL_UPDATE = 0 << 4
MEDIUM_UPDATE = 2 << 4
DITHER = 1 << 8

conversion_factor = 3.3 / 65536

_current_mode = MEDIUM_UPDATE
mode(MEDIUM_UPDATE, True)

builtins.screen = image(display.WIDTH, display.HEIGHT, memoryview(display))
screen.font = DEFAULT_FONT
screen.pen = BG


# Build in some badgeware helpers, so we don't have to "bw.lores" etc
# note HIRES and LORES and mode are currently unused for Blinky
for k in ("mode", "HIRES", "LORES", "FAST_UPDATE", "FULL_UPDATE", "MEDIUM_UPDATE", "DITHER", "SpriteSheet", "load_font", "rom_font", "text_tokenise", "text_draw"):
    setattr(builtins, k, locals()[k])

# Hoist image anti-aliasing constants
builtins.OFF = image.OFF
builtins.X2 = image.X2
builtins.X4 = image.X4

# Finally, build in badgeware as "bw" for less frequently used things
builtins.bw = sys.modules["badgeware"]


if __name__ == "__main__":
    fatal_error("Hello from badgeware.py", "Why are you running me?")
