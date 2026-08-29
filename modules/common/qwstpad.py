import struct
from collections import OrderedDict

from micropython import const
from machine import I2C

__version__ = "0.0.1"

# Constants
NUM_LEDS = const(4)
NUM_BUTTONS = const(10)

DEFAULT_ADDRESS = const(0x21)
ALT_ADDRESS_1 = const(0x23)
ALT_ADDRESS_2 = const(0x25)
ALT_ADDRESS_3 = const(0x27)
ADDRESSES = (DEFAULT_ADDRESS, ALT_ADDRESS_1, ALT_ADDRESS_2, ALT_ADDRESS_3)
I2C_PINS = {"id": 0, "sda": 4, "scl": 5}    # The I2C pins the QwSTPad is connected to
i2c = I2C(**I2C_PINS)                           # The I2C instance to pass to all QwSTPads


class QwSTPad:
    # Registers
    INPUT_PORT0 = const(0x00)
    INPUT_PORT1 = const(0x01)
    OUTPUT_PORT0 = const(0x02)
    OUTPUT_PORT1 = const(0x03)
    POLARITY_PORT0 = const(0x04)
    POLARITY_PORT1 = const(0x05)
    CONFIGURATION_PORT0 = const(0x06)
    CONFIGURATION_PORT1 = const(0x07)

    # Mappings
    BUTTON_MAPPING = OrderedDict({"A": 0xE, "B": 0xC, "X": 0xF, "Y": 0xD,
                                  "U": 0x1, "D": 0x4, "L": 0x2, "R": 0x3,
                                  "+": 0xB, "-": 0x5
                                  })
    LED_MAPPING = (0x6, 0x7, 0x9, 0xA)

    def __init__(self, i2c, address=DEFAULT_ADDRESS, show_address=True):
        if address not in ADDRESSES:
            raise ValueError("address is not valid. Expected: 0x21, 0x23, 0x25, or 0x27")

        self.__i2c = i2c
        self.__address = address

        # Set up the TCA9555 with the correct input and output pins
        self.__reg_write_uint16(self.__i2c, self.__address, self.CONFIGURATION_PORT0, 0b11111001_00111111)
        self.__reg_write_uint16(self.__i2c, self.__address, self.POLARITY_PORT0, 0b11111000_00111111)
        self.__reg_write_uint16(self.__i2c, self.__address, self.OUTPUT_PORT0, 0b00000110_11000000)

        self.__button_states = OrderedDict({})
        for key, _ in self.BUTTON_MAPPING.items():
            self.__button_states[key] = False

        self.__led_states = 0b0000
        if show_address:
            self.set_leds(self.address_code())

        self.buttons = self.read_buttons()
        self.__pressed = {}
        self.__released = {}
        self.__changed = {}
        self.__held = {}
        self.update_buttons()

    def address_code(self):
        return self.__change_bit(0x0000, ADDRESSES.index(self.__address), True)

    def read_buttons(self):
        state = self.__reg_read_uint16(self.__i2c, self.__address, self.INPUT_PORT0)
        for key, value in self.BUTTON_MAPPING.items():
            self.__button_states[key] = self.__get_bit(state, value)
        return self.__button_states

    def set_leds(self, states):
        self.__led_states = states & 0b1111
        self.__update_leds()

    def set_led(self, led, state):
        if led < 1 or led > NUM_LEDS:
            raise ValueError("'led' out of range. Expected 1 to 4")

        self.__led_states = self.__change_bit(self.__led_states, led - 1, state)
        self.__update_leds()

    def clear_leds(self):
        self.__led_states = 0b0000
        self.__update_leds()

    def __update_leds(self):
        output = 0
        for i in range(NUM_LEDS):
            output = self.__change_bit(output, self.LED_MAPPING[i], not self.__get_bit(self.__led_states, i))
        self.__reg_write_uint16(self.__i2c, self.__address, self.OUTPUT_PORT0, output)

    def __get_bit(self, num, bit_pos):
        return (num & (1 << bit_pos)) != 0

    def __change_bit(self, num, bit_pos, state):
        return num | (1 << bit_pos) if state else num & ~(1 << bit_pos)

    def __reg_write_uint16(self, i2c, address, reg, value):
        buffer = struct.pack("<H", value)
        i2c.writeto_mem(address, reg, buffer)

    def __reg_read_uint16(self, i2c, address, reg):
        buffer = i2c.readfrom_mem(address, reg, 2)
        return struct.unpack("<H", buffer)[0]

    def update_buttons(self):
        old_values = {}
        for key, value in self.buttons.items():
            old_values[key] = value

        self.buttons = self.read_buttons()

        for key, value in self.buttons.items():
            if not old_values[key] and not value:
                self.__pressed[key] = False
                self.__released[key] = False
                self.__changed[key] = False
                self.__held[key] = False
            if not old_values[key] and value:
                self.__pressed[key] = True
                self.__released[key] = False
                self.__changed[key] = True
                self.__held[key] = True
            if old_values[key] and not value:
                self.__pressed[key] = False
                self.__released[key] = True
                self.__changed[key] = True
                self.__held[key] = False
            if old_values[key] and value:
                self.__pressed[key] = False
                self.__released[key] = False
                self.__changed[key] = False
                self.__held[key] = True

    def pressed(self, button=None):
        if button is None:
            return True in self.__pressed.values()
        return self.__pressed[button]

    def released(self, button=None):
        if button is None:
            return True in self.__released.values()
        return self.__released[button]

    def changed(self, button=None):
        if button is None:
            return True in self.__changed.values()
        return self.__changed[button]

    def held(self, button=None):
        if button is None:
            return True in self.__held.values()
        return self.__held[button]


class Gamepadhelper:
    def __init__(self):
        self.pads = []
        self.pads_count = 0
        self.get_gamepads()

    def get_gamepads(self):
        pads_count = 0

        # Create a player for each connected QwSTPad
        for i in range(len(ADDRESSES)):
            try:
                self.pads.append(QwSTPad(i2c, ADDRESSES[i]))
                print(f"P{i + 1}: Connected")
                pads_count += 1
            except OSError:
                self.pads.append(None)
                print(f"P{i + 1}: Not Connected")

        self.pads_count = pads_count
