import network
from machine import Pin, Timer, ADC, I2C
import time
from pcf85063a import PCF85063A
import badgeware #noqa F401
import powman
import os
import gc
import ssd1680

"""

Hardware Error Codes:

E1 - Wireless scan fail - unable to detect networks.
E2 - Charging Fail
E3 - RTC Alarm was in a triggeered state in pre checks.
E4 - RTC Alarm didn't trigger after timer
E5 - VBUS DETECT Fail or timed out
E6 - VBUS Detect was in a triggered state in pre checks.
E7 - VBAT SENSE reading was out of range
E8 - SW_POWER_EN function test failed
E10 - MAC Address invalid
E11 - Time out during button test
E17 - Failed to start CYW43 (RM2 Module)
E18 - PSRAM Test Failure

"""

display = ssd1680.SSD1680()
display.speed(2)

WIDTH, HEIGHT = screen.width, screen.height

large_font = font.smart
screen.font = large_font

WHITE = color.white
BLACK = color.black
GRAY = color.dark_grey

CL = [Pin(0, Pin.OUT), Pin(1, Pin.OUT),
      Pin(2, Pin.OUT), Pin(3, Pin.OUT)]

charge_stat = Pin.board.CHARGE_STAT
charge_stat.init(mode=Pin.IN)
vbus_detect = Pin.board.VBUS_DETECT
sw_int = Pin.board.BUTTON_INT
rtc_alarm = Pin.board.RTC_ALARM
vbat = ADC(Pin.board.VBAT_SENSE)

up = Pin.board.BUTTON_UP
down = Pin.board.BUTTON_DOWN
a = Pin.board.BUTTON_A
b = Pin.board.BUTTON_B
c = Pin.board.BUTTON_C
home = Pin.board.BUTTON_HOME
power = Pin.board.POWER_EN


def centre_text(text, y):
    tx = (WIDTH // 2) - (screen.measure_text(text)[0] / 2)
    screen.text(text, tx, y)


class Tests:
    def __init__(self):

        self.wifi_pass = None
        self.buttons_pass = False
        self.vbus_pass = False
        self.rtc_pass = None

        self.wlan = network.WLAN(network.WLAN.IF_STA)
        self.wlan.active(True)
        self.mac = self.wlan.config("mac")

        sw_int.irq(self.btn_handler)

        # RTC Setup
        self.rtc = PCF85063A(I2C())
        self.rtc.clear_timer_flag()
        self.rtc.enable_timer_interrupt(True)
        self.rtc_start = time.time()

        # We want to check the RTC alarm has trigger
        self.rtc_timer = Timer()

        # Raspberry Pi Vendor ID
        self.vendor = "28:CD:C1"

        # a dict to store the button name, state and label location on screen
        self.buttons = {"A": [False, (36, 150)], "B": [False, (120, 150)],
                        "C": [False, (202, 150)], "UP": [False, (WIDTH - 25, 35)],
                        "DOWN": [False, (WIDTH - 25, 120)], "HOME": [False, (WIDTH // 2 - 15, 10)]}

    def test_wireless(self):
        try:
            if self.wifi_pass is None:
                data = ":".join([f"{b:02X}" for b in self.mac])
                print(self.wlan.config("mac"))
                results = self.wlan.scan()

                if len(results) == 0:
                    raise Exception("E1")

                if data[:8] != self.vendor:
                    raise Exception("E10")

                self.wifi_pass = True
        except OSError:
            raise Exception("E17") from None

    def display_error(self, error):
        screen.pen = WHITE
        screen.clear()
        screen.pen = BLACK
        centre_text(str(error), (HEIGHT / 2) - 10)
        display.update()

    def test_buttons(self):
        # Check if all buttons have been pressed
        if not self.buttons_pass:
            for button in self.buttons:
                if not self.buttons[button][0]:
                    return

            self.buttons_pass = True
            print("BUTTONS: OK!")

    def test_charge_stat(self):
        # if battery charging is not detected
        # raise an exception and end the test
        if charge_stat.value() == 1:
            raise Exception("E2")

    def test_vbat(self):
        voltage = vbat.read_u16() * (3.3 / 65536) * 2
        if voltage > 4.2 or voltage < 3.6:
            raise Exception("E7")

    def test_psram(self):
        ram_free = round(gc.mem_free() / 1000000, 1)

        if ram_free < 8.2 or not powman._test_psram_cs():  # noqa SLF001
            raise Exception("E18")

    # Toggle the case lights on the back of the badge
    def cl_toggle(self):
        for led in CL:
            led.toggle()

    def clear_flag(self):
        # Now the test has complete, we can remove the flag.
        try:
            os.remove("hardware_test.txt")
        except OSError:
            pass

    # Handle the user exiting the test
    # This is only enabled once the function tests have passed
    def exit_handler(self, _pin):
        # The test has passed so we can clear the flag.
        self.clear_flag()

        # Time to sleep now!
        powman.sleep()

    def run(self):

        try:

            # We want to check we can toggle the SW_POWER_EN pin.
            # We're going to do it here before the rest of test starts
            power.off()
            if power.value():
                # Not that you'd see this error with no LED power xD
                raise Exception("E8")

            power.on()
            if not power.value():
                raise Exception("E8")

            self.test_psram()

            # Set the timers for the RTC test
            self.rtc.set_timer(2)
            self.rtc_timer.init(mode=Timer.ONE_SHOT, period=2100, callback=self.test_rtc)

            # If the pin for RTC alarm is already low, there's a problem.
            if rtc_alarm.value() == 0:
                raise Exception("E3")

            # If the pin for VBUS DETECT is already low, there's a problem.
            if vbus_detect.value() == 0:
                raise Exception("E6")

            self.test_wireless()
            self.test_charge_stat()

            if not self.vbus_pass:
                self.test_vbus()

            if self.rtc_pass is False:
                raise Exception("E4")

            self.draw()

            button_timeout = time.time()
            while True:
                if time.time() - button_timeout > 10:
                    raise Exception("E11")

                self.test_buttons()

                # Home button can't interrupt so we check it here.
                if not int(home.value()):
                    self.buttons["HOME"][0] = True

                if self.buttons_pass:
                    break

        except Exception as e:   # noqa BLE001
            self.display_error(e)
            powman.sleep()

        b.irq(self.exit_handler)

        # The test has passed now
        screen.pen = WHITE
        screen.clear()
        screen.pen = BLACK
        centre_text("PASS", 50)
        centre_text("Press B to sleep.", 80)
        display.update()

        # We want to make sure the case LEDs are on
        # so the user can easily tell that the unit has entered sleep mode
        for led in CL:
            led.on()

        # Waiting here now for the user to press the B button
        while True:
            pass

    # Interrupt based button testing checks the button gpio
    # and that each button is able to trigger sw_int
    def btn_handler(self, _pin):

        self.cl_toggle()

        if not int(a.value()):
            self.buttons["A"][0] = True

        if not int(b.value()):
            self.buttons["B"][0] = True

        if not int(c.value()):
            self.buttons["C"][0] = True

        if not int(up.value()):
            self.buttons["UP"][0] = True

        if not int(down.value()):
            self.buttons["DOWN"][0] = True

    def test_rtc(self, _t):
        # By the time this handler is used
        # the RTC alarm should have triggered
        self.rtc_pass = not rtc_alarm.value()
        self.rtc_timer.deinit()

    def test_vbus(self):

        screen.pen = WHITE
        screen.clear()
        screen.pen = BLACK
        screen.text("< Remove USB to continue", 5, 80)
        display.update()

        start_time = time.time()
        while True:
            # Time out to catch the user not removing the USB
            # Or to end the test if there's a failure on VBUS_DETECT
            if time.time() - start_time < 5:
                self.cl_toggle()
                # We're checking status of the USB connection here.
                # If it changes we're going to assume the user removed it.
                if vbus_detect.value() == 0:
                    self.test_vbat()
                    self.vbus_pass = True
                    break
            else:
                raise Exception("E5")

    def draw(self):
        # Clear screen and display title
        screen.pen = WHITE
        screen.clear()
        screen.pen = BLACK

        centre_text("Press all face buttons + HOME", 80)

        # Draw button presses
        screen.pen = GRAY
        for button in sorted(self.buttons):
            pressed = self.buttons[button][0]
            if not pressed:
                x, y = self.buttons[button][1]
                screen.shape(shape.rounded_rectangle(x, y, 20, 20, 4))

        display.update()


t = Tests()

t.run()
