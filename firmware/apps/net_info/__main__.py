import ezwifi
from picovector import ANTIALIAS_BEST, PicoVector, Polygon, Transform

import badger2350
from badger2350 import HEIGHT, WIDTH

# Display Setup
display = badger2350.Badger2350()
# display.led(0)

# Pico Vector
vector = PicoVector(display.display)
vector.set_antialiasing(ANTIALIAS_BEST)
t = Transform()
vector.set_transform(t)

TITLE_BAR = Polygon()
TITLE_BAR.rectangle(2, 2, 260, 16, (8, 8, 8, 8))
TITLE_BAR.circle(253, 10, 4)
IP_BAR = Polygon()
IP_BAR.rectangle(2, 82, 260, 40, (8, 8, 8, 8))


def draw_header():

    # Page Header
    display.set_pen(15)
    display.clear()
    display.set_pen(0)

    display.set_pen(0)
    vector.draw(TITLE_BAR)
    display.set_pen(3)

    display.text("badgerOS", 7, 6, WIDTH, 1)
    display.text("Network Details", WIDTH - 100, 6, WIDTH, 1)
    display.set_pen(0)


def connect_handler(wifi):
    # Make sure the LED is on to signal the WiFi has connected
    # display.led(128)

    # Draw the title header
    draw_header()

    display.set_pen(0)
    vector.draw(IP_BAR)

    ip = wifi.ipv4()

    text_w = display.measure_text(ip, 4)
    text_x = WIDTH // 2 - text_w // 2
    display.set_pen(3)
    display.text(ip, text_x, HEIGHT // 2, WIDTH, 4)

    display.set_pen(0)
    display.text("Your local IP:", text_x, 65, WIDTH, 2)

    display.update()


def failed_handler(_wifi):
    # Make sure the LED is OFF to signal the WiFi has not connected
    # display.led(0)

    # Draw the title header
    draw_header()

    display.set_pen(0)
    vector.draw(IP_BAR)

    ip = "Unavailable"

    text_w = display.measure_text(ip, 4)
    text_x = WIDTH // 2 - text_w // 2
    display.set_pen(3)
    display.text(ip, text_x, HEIGHT // 2, WIDTH, 4)

    display.set_pen(0)
    display.text("Your local IP:", text_x, 65, WIDTH, 2)

    display.text("Check Your 'secrets.py' and try again.", text_x, 127, WIDTH - 10, 2)

    display.update()


try:
    ezwifi.connect(verbose=True, retries=3, connected=connect_handler, failed=failed_handler)
except ValueError:
    failed_handler(False)

# Call halt in a loop, on battery this switches off power.
# On USB, the app will exit when A+C is pressed because the launcher picks that up.
while True:
    # display.keepalive()  # TODO: No longer a problem because "halt" puts the board into powman sleep()
    display.halt()
