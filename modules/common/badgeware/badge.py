import _input
import os
import builtins
import machine
import powman
import binascii

MODEL = os.uname().machine[9:-17].lower()
UID = binascii.hexlify(machine.unique_id()).decode("ASCII")

builtins.LORES = 0b00
builtins.HIRES = 0b01
builtins.VSYNC = 0b10

builtins.FAST_UPDATE = 3 << 4
builtins.FULL_UPDATE = 0 << 4
builtins.MEDIUM_UPDATE = 2 << 4
builtins.DITHER = 1 << 8

builtins.BUTTON_A = _input.BUTTON_A
builtins.BUTTON_B = _input.BUTTON_B
builtins.BUTTON_C = _input.BUTTON_C
builtins.BUTTON_UP = _input.BUTTON_UP
builtins.BUTTON_DOWN = _input.BUTTON_DOWN
builtins.BUTTON_HOME = _input.BUTTON_HOME


VBAT_SENSE = machine.ADC(machine.Pin.board.VBAT_SENSE)
VBUS_DETECT = machine.Pin.board.VBUS_DETECT
CHARGE_STAT = machine.Pin.board.CHARGE_STAT
SENSE_1V1 = machine.ADC(machine.Pin.board.SENSE_1V1)

BAT_MAX = 4.10
BAT_MIN = 3.00

conversion_factor = 3.3 / 65536

if MODEL == "tufty":
    LIGHT_SENSOR = machine.ADC(machine.Pin("LIGHT_SENSE"))
else:
    LIGHT_SENSOR = None


def sample_adc_u16(adc, samples=1):
    val = []
    for _ in range(samples):
        val.append(adc.read_u16())
    return sum(val) / len(val)


class Badge():
    def  __init__(self):
        if MODEL == "badger":
            self._background = color.white
            self._foreground = color.black
        else:
            self._background = color.black
            self._foreground = color.white
        self._current_mode = None

        self._case_lights = [
            machine.PWM(machine.Pin.board.CL0),
            machine.PWM(machine.Pin.board.CL1),
            machine.PWM(machine.Pin.board.CL2),
            machine.PWM(machine.Pin.board.CL3)
        ]
        for led in self._case_lights:
            led.freq(500)

    @property
    def ticks(self):
        return _input.ticks

    @property
    def ticks_delta(self):
        return _input.ticks_delta

    def poll(self):
        _input.poll()

    # returns either badger, tufty, or blinky
    @property
    def model(self):
        return MODEL

    @property
    def uid(self):
        return UID

    def background(self, *args):
        if len(args) == 0:
            return self._background
        self._background = args[0]
        return None

    def foreground(self, *args):
        if len(args) == 0:
            return self._foreground
        self._foreground = args[0]
        return None

    def mode(self, mode=None):
        if mode is None:
            return self._current_mode

        if mode == self._current_mode:
            return None

        self._current_mode = mode

        if MODEL == "tufty":
            display.fullres(bool(mode & HIRES))
            display.set_vsync(bool(mode & VSYNC))

        elif MODEL == "badger":
            display.speed((self._current_mode >> 4) & 0xf)

        # TODO: Mutate the existing screen object?
        font = getattr(getattr(builtins, "screen", None), "font", None)
        brush = getattr(getattr(builtins, "screen", None), "pen", None)
        builtins.screen = image(display.WIDTH, display.HEIGHT, memoryview(display))
        screen.font = font if font is not None else rom_font.sins
        screen.pen = brush if brush is not None else self._foreground

        return None

    def battery_voltage(self):
        # Get the average reading over 20 samples from our VBAT and VREF
        voltage = sample_adc_u16(VBAT_SENSE, 10) * conversion_factor * 2
        vref = sample_adc_u16(SENSE_1V1, 10) * conversion_factor
        return  voltage / vref * 1.1

    def usb_connected(self):
        return bool(VBUS_DETECT.value())

    def battery_level(self):
        # Use the battery voltage to estimate the remaining percentage
        return min(100, max(0, round(123 - (123 / pow((1 + pow((self.battery_voltage() / 3.2), 80)), 0.165)))))

    def is_charging(self):
        # We only want to return the charge status if the USB cable is connected.
        if VBUS_DETECT.value():
            return not CHARGE_STAT.value()

        return False

    def disk_free(mountpoint="/"):
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

    def light_level(self):
        # TODO: Returning the raw u16 is a little meh here, can we do an approx lux conversion?
        if LIGHT_SENSOR is None:
            raise RuntimeError("Light level not supported!")
        return LIGHT_SENSOR.read_u16()

    def pressed(self, button=None):
        if button is None:
            return _input.pressed
        return button in _input.pressed

    def held(self, button=None):
        if button is None:
            return _input.held
        return button in _input.held

    def released(self, button=None):
        if button is None:
            return _input.released
        return button in _input.released

    def changed(self, button=None):
        if button is None:
            return _input.changed
        return button in _input.changed

    def resolution(self):
        return screen.width, screen.height

    def set_caselights(self, v1, v2=None, v3=None, v4=None):
        if v2 is None:
            v4 = v3 = v2 = v1

        self._case_lights[0].duty_u16(int(v1 * 65535))
        self._case_lights[1].duty_u16(int(v2 * 65535))
        self._case_lights[2].duty_u16(int(v3 * 65535))
        self._case_lights[3].duty_u16(int(v4 * 65535))

    def get_caselights(self):
        return [light.duty_u16() / 65535 for light in self._case_lights]

    def sleep(self, duration=None):
        powman.goto_dormant_for(duration) if duration else powman.sleep()

    def wake_reason(self):
        pass

    def woken_by_button(self):
        return powman.get_wake_reason() in (
            powman.WAKE_BUTTON_A,
            powman.WAKE_BUTTON_B,
            powman.WAKE_BUTTON_C,
            powman.WAKE_BUTTON_UP,
            powman.WAKE_BUTTON_DOWN,
        )

    def pressed_to_wake(self, button):
        # TODO: BUTTON_HOME cannot be a wake button
        # so maybe raise an exception
        return button in powman.get_wake_buttons()

    def woken_by_reset(self):
        return powman.get_wake_reason() == 255


builtins.badge = Badge()
