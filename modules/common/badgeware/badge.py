import _input
import os
import builtins
import machine
import powman
import binascii
import time

from qwstpad import QwSTPad, ADDRESSES as PAD_ADDRESSES

MODEL = os.uname().machine[9:-17].lower()
UID = binascii.hexlify(machine.unique_id()).decode("ascii")

builtins.LORES = 0b00
builtins.HIRES = 0b01
builtins.VSYNC = 0b10

builtins.FAST_UPDATE = 3 << 4
builtins.FULL_UPDATE = 0 << 4
builtins.MEDIUM_UPDATE = 2 << 4
builtins.DITHER = 1 << 8

builtins.NON_BLOCKING = 1 << 9


class Action:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


builtins.BUTTON_A = machine.Pin.board.BUTTON_A
builtins.BUTTON_B = machine.Pin.board.BUTTON_B
builtins.BUTTON_C = machine.Pin.board.BUTTON_C
builtins.BUTTON_UP = machine.Pin.board.BUTTON_UP
builtins.BUTTON_DOWN = machine.Pin.board.BUTTON_DOWN
builtins.BUTTON_HOME = machine.Pin.board.BUTTON_HOME

PAD_UP = Action("PAD_UP")
PAD_DOWN = Action("PAD_DOWN")
PAD_LEFT = Action("PAD_LEFT")
PAD_RIGHT = Action("PAD_RIGHT")
PAD_A = Action("PAD_A")
PAD_B = Action("PAD_B")
PAD_X = Action("PAD_X")
PAD_Y = Action("PAD_Y")
PAD_PLUS = Action("PAD_PLUS")
PAD_MINUS = Action("PAD_MINUS")

builtins.PAD_UP = PAD_UP
builtins.PAD_DOWN = PAD_DOWN
builtins.PAD_LEFT = PAD_LEFT
builtins.PAD_RIGHT = PAD_RIGHT
builtins.PAD_A = PAD_A
builtins.PAD_B = PAD_B
builtins.PAD_X = PAD_X
builtins.PAD_Y = PAD_Y
builtins.PAD_PLUS = PAD_PLUS
builtins.PAD_MINUS = PAD_MINUS

# QwSTPad.BUTTON_MAPPING key for each pad button
PAD_BUTTONS = (
    ("U", PAD_UP),
    ("D", PAD_DOWN),
    ("L", PAD_LEFT),
    ("R", PAD_RIGHT),
    ("A", PAD_A),
    ("B", PAD_B),
    ("X", PAD_X),
    ("Y", PAD_Y),
    ("+", PAD_PLUS),
    ("-", PAD_MINUS),
)

PAD_MAP = {
    PAD_UP: BUTTON_UP,
    PAD_DOWN: BUTTON_DOWN,
    PAD_LEFT: BUTTON_A,
    PAD_RIGHT: BUTTON_C,
    PAD_B: BUTTON_B,
}

DIRECTION_UP = (BUTTON_UP, PAD_UP)
DIRECTION_DOWN = (BUTTON_DOWN, PAD_DOWN)
DIRECTION_LEFT = (BUTTON_A, PAD_LEFT)
DIRECTION_RIGHT = (BUTTON_C, PAD_RIGHT)

QWST_I2C_ID = 0

# One pad address is looked for, or health checked, per interval
PAD_SERVICE_MS = 250


VBAT_SENSE = machine.ADC(machine.Pin.board.VBAT_SENSE)
VBUS_DETECT = machine.Pin.board.VBUS_DETECT
CHARGE_STAT = machine.Pin.board.CHARGE_STAT
SENSE_1V1 = machine.ADC(machine.Pin.board.SENSE_1V1)

BAT_MAX = 4.10
BAT_MIN = 3.00

TEXT_START = vec2(0, 0)

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


def _merge(*groups):
    merged = []

    for group in groups:
        for action in group:
            if action not in merged:
                merged.append(action)

    return tuple(merged)


def _pad_table(mapping):
    table = []

    for key, action in PAD_BUTTONS:
        table.append((1 << QwSTPad.BUTTON_MAPPING[key], action, mapping.get(action)))

    return tuple(table)


def _pad_actions(bits, table):
    # The pad's own buttons, and the Tufty buttons they are mapped to
    if not bits:
        return (), ()

    actions = []
    mapped = []

    for bit, action, button in table:
        if bits & bit:
            actions.append(action)
            if button is not None and button not in mapped:
                mapped.append(button)

    return tuple(actions), tuple(mapped)


class Controls:
    def __init__(self):
        self._held = ()
        self._pressed = ()
        self._released = ()
        self._changed = ()

    def set_state(self, held, pressed, released, changed):
        self._held = held
        self._pressed = pressed
        self._released = released
        self._changed = changed

    def held(self, action=None):
        return self._held if action is None else action in self._held

    def pressed(self, action=None):
        return self._pressed if action is None else action in self._pressed

    def released(self, action=None):
        return self._released if action is None else action in self._released

    def changed(self, action=None):
        return self._changed if action is None else action in self._changed

    def _heading(self, actions):
        return any(action in self._held for action in actions)

    def direction(self):
        # A pad D-pad press also reports as a Tufty button, so count each way once
        x = self._heading(DIRECTION_RIGHT) - self._heading(DIRECTION_LEFT)
        y = self._heading(DIRECTION_DOWN) - self._heading(DIRECTION_UP)

        if x == 0 and y == 0:
            return vec2(0, 0)

        return vec2(x, y).normalized()


class Pad(Controls):
    def __init__(self, i2c, address):
        super().__init__()
        self.address = address
        self.connected = False
        self._i2c = i2c
        self._device = None
        self._buttons = 0
        self._table = ()

        # True while anything is held or changed this frame
        self.active = False

        # This player's own map, or None to follow badge.pad_map()
        self.mapping = None

        # The Tufty buttons this pad's buttons are mapped to, merged only into badge.all
        self.mapped = Controls()

    def remap(self, default):
        self._table = _pad_table(default if self.mapping is None else self.mapping)

    def leds(self, states):
        # Kept by the driver and restored if the pad is re-plugged
        if self._device is None:
            return
        try:
            self._device.set_leds(states)
        except OSError:
            pass

    # service() and update() are called by badge.poll()
    def service(self):
        try:
            if self.connected:
                if not self._device.check():
                    self._device.setup()
            elif self._device is None:
                self._device = QwSTPad(self._i2c, self.address)
                self.connected = True
            else:
                self._device.setup()
                self.connected = True
        except OSError:
            self.connected = False

    def update(self):
        buttons = 0

        if self.connected:
            try:
                buttons = self._device.read_mask()
            except OSError:
                # Unplugged: dropping to no buttons releases anything held
                self.connected = False

        changed = buttons ^ self._buttons
        self._buttons = buttons

        if not buttons and not changed:
            if self.active:
                self.set_state((), (), (), ())
                self.mapped.set_state((), (), (), ())
                self.active = False
            return

        table = self._table
        held, held_mapped = _pad_actions(buttons, table)
        pressed, pressed_mapped = _pad_actions(buttons & changed, table)
        released, released_mapped = _pad_actions(~buttons & changed, table)
        flipped, flipped_mapped = _pad_actions(changed, table)

        self.set_state(held, pressed, released, flipped)
        self.mapped.set_state(held_mapped, pressed_mapped, released_mapped, flipped_mapped)
        self.active = True


class Badge():
    def  __init__(self):
        if MODEL == "badger":
            self.default_clear = color.white
            self.default_pen = color.black
        else:
            self.default_clear = color.black
            self.default_pen = color.white

        # current display mode
        self._current_mode = None

        # either badger, tufty, or blinky
        self.model = MODEL

        # the system
        self.uid = UID

        # track first display update, for badger
        self.first_update = True

        self._case_light_values = [
            0, 0, 0, 0
        ]
        self._case_lights = [
            machine.PWM(machine.Pin.board.CL0),
            machine.PWM(machine.Pin.board.CL1),
            machine.PWM(machine.Pin.board.CL2),
            machine.PWM(machine.Pin.board.CL3)
        ]
        for led in self._case_lights:
            led.freq(500)
            led.duty_u16(0)

        self.buttons = Controls()
        self.all = Controls()

        # All pads merged, for badge.all
        self._pad = Controls()
        self._pad_mapped = Controls()

        qwst_i2c = machine.I2C(QWST_I2C_ID)
        self.pad = tuple(Pad(qwst_i2c, address) for address in PAD_ADDRESSES)
        self._pad_map = dict(PAD_MAP)
        self._refresh_pad_maps()

        for pad in self.pad:
            pad.service()

        self._pad_service_at = 0
        self._pad_service_next = 0
        self._pads_connected = self.pad_connected()
        self._pad_active = False

    @property
    def ticks(self):
        return _input.ticks

    @property
    def ticks_delta(self):
        return _input.ticks_delta

    def poll(self):
        _input.poll()
        self._poll_pads()

        held = _input.held
        pressed = _input.pressed
        released = _input.released
        changed = _input.changed
        self.buttons.set_state(held, pressed, released, changed)

        if not self._pad_active:
            self.all.set_state(held, pressed, released, changed)
            return

        pad = self._pad
        mapped = self._pad_mapped
        self.all.set_state(
            _merge(held, mapped.held(), pad.held()),
            _merge(pressed, mapped.pressed(), pad.pressed()),
            _merge(released, mapped.released(), pad.released()),
            _merge(changed, mapped.changed(), pad.changed()),
        )

    def _poll_pads(self):
        pads = self.pad
        now = time.ticks_ms()

        # Look for a missing pad
        if time.ticks_diff(now, self._pad_service_at) >= PAD_SERVICE_MS:
            self._pad_service_at = now
            pads[self._pad_service_next].service()
            self._pad_service_next = (self._pad_service_next + 1) % len(pads)
            self._pads_connected = self.pad_connected()

        # Nothing plugged in and nothing left to release
        if not self._pads_connected and not self._pad_active:
            return

        active = None
        count = 0

        for pad in pads:
            # A pad that has just gone still needs one update to release its buttons
            if pad.connected or pad.active:
                pad.update()
                if pad.active:
                    active = pad
                    count += 1

        was_active = self._pad_active
        self._pad_active = count > 0

        # Merging allocates, so only do it when more than one pad has something to report
        if count == 0:
            if was_active:
                self._pad.set_state((), (), (), ())
                self._pad_mapped.set_state((), (), (), ())
        elif count == 1:
            mapped = active.mapped
            self._pad.set_state(active.held(), active.pressed(), active.released(), active.changed())
            self._pad_mapped.set_state(mapped.held(), mapped.pressed(), mapped.released(), mapped.changed())
        else:
            self._pad.set_state(
                _merge(*[pad.held() for pad in pads]),
                _merge(*[pad.pressed() for pad in pads]),
                _merge(*[pad.released() for pad in pads]),
                _merge(*[pad.changed() for pad in pads]),
            )
            self._pad_mapped.set_state(
                _merge(*[pad.mapped.held() for pad in pads]),
                _merge(*[pad.mapped.pressed() for pad in pads]),
                _merge(*[pad.mapped.released() for pad in pads]),
                _merge(*[pad.mapped.changed() for pad in pads]),
            )

    def pad_connected(self, player=None):
        if player is None:
            return any(pad.connected for pad in self.pad)
        return self.pad[player].connected

    def pad_map(self, mapping=None, player=None):
        if mapping is None:
            if player is None or self.pad[player].mapping is None:
                return dict(self._pad_map)
            return dict(self.pad[player].mapping)

        mapping = dict(mapping)

        if any(button == BUTTON_HOME for button in mapping.values()):
            raise ValueError("Pads can't map to BUTTON_HOME!")

        if player is None:
            self._pad_map = mapping
        else:
            self.pad[player].mapping = mapping

        self._refresh_pad_maps()
        return None

    def _refresh_pad_maps(self):
        for pad in self.pad:
            pad.remap(self._pad_map)

    def direction(self):
        return self.all.direction()

    @property
    def resolution(self):
        return screen.width, screen.height

    def clear(self):
        if self.default_clear is not None:
            screen.pen = self.default_clear
            screen.clear()
        screen.pen = self.default_pen
        screen.cursor = TEXT_START
        return True

    def update(self):
        # Do a full update to avoid ghosting when switching apps
        if MODEL == "badger" and badge.first_update:
            display.speed(0)

        # Perform the dither on the screen raw buffer
        if badge.mode() & DITHER:
            screen.dither()

        display.update()
        badge.clear()
        badge.poll()

        # Set the update back to the user specified speed
        if MODEL == "badger" and badge.first_update:
            display.speed((badge.mode() >> 4) & 0xf)

        badge.first_update = False
        return True

    def mode(self, mode=None):
        if mode is None:
            return self._current_mode

        if mode == self._current_mode:
            return None

        self._current_mode = mode

        if MODEL == "tufty":
            display.fullres(bool(mode & HIRES))
            display.set_vsync(bool(mode & VSYNC))
            display.set_framerate(90)

        elif MODEL == "badger":
            display.blocking(not bool(self._current_mode & NON_BLOCKING))
            display.speed((self._current_mode >> 4) & 0xf)

        if MODEL == "tufty" or getattr(builtins, "screen", None) is None:
            prev_font = getattr(getattr(builtins, "screen", None), "font", None)
            brush = getattr(getattr(builtins, "screen", None), "pen", None)
            builtins.screen = image(display.WIDTH, display.HEIGHT, memoryview(display))
            screen.font = prev_font if prev_font is not None else font.sins
            screen.pen = brush if brush is not None else self.default_pen

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

    def disk_free(self, mountpoint="/system"):
        # f_bfree and f_bavail should be the same?
        # f_files, f_ffree, f_favail and f_flag are unsupported.
        f_bsize, f_frsize, f_blocks, f_bfree = os.statvfs(mountpoint)[:4]

        f_total_size = f_frsize * f_blocks
        f_total_free = f_bsize * f_bfree

        return f_total_size, f_total_size - f_total_free, f_total_free

    def light_level(self):
        # TODO: Returning the raw u16 is a little meh here, can we do an approx lux conversion?
        if LIGHT_SENSOR is None:
            raise RuntimeError("Light level not supported!")
        return LIGHT_SENSOR.read_u16()

    def pressed(self, button=None):
        return self.all.pressed(button)

    def held(self, button=None):
        return self.all.held(button)

    def released(self, button=None):
        return self.all.released(button)

    def changed(self, button=None):
        return self.all.changed(button)

    def caselights(self, *args):
        if args:
            self._case_light_values[:] = (args[0], ) * 4 if len(args) == 1 else args

            for idx, cl in enumerate(self._case_lights):
                cl.duty_u16(int(self._case_light_values[idx] ** 2.2 * 65535))

        return list(self._case_light_values)

    def sleep(self, duration=None):
        powman.goto_dormant_for(duration) if duration else powman.sleep()

    def wake_reason(self):
        return powman.get_wake_reason()

    def woken_by_button(self):
        return powman.get_wake_reason() in (
            powman.WAKE_BUTTON_A,
            powman.WAKE_BUTTON_B,
            powman.WAKE_BUTTON_C,
            powman.WAKE_BUTTON_UP,
            powman.WAKE_BUTTON_DOWN,
        )

    def pressed_to_wake(self, button):
        return button in powman.get_wake_buttons()

    def woken_by_reset(self):
        return powman.get_wake_reason() == 255


builtins.badge = Badge()
