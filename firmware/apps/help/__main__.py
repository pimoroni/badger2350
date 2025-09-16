from picovector import ANTIALIAS_BEST, PicoVector, Polygon, Transform

import badger2350
from badger2350 import WIDTH

TEXT_SIZE = 0.45
LINE_HEIGHT = 20

display = badger2350.Badger2350()
# display.led(128)
# display.set_thickness(2)

# Pico Vector
vector = PicoVector(display.display)
vector.set_antialiasing(ANTIALIAS_BEST)
t = Transform()

TITLE_BAR = Polygon()
TITLE_BAR.rectangle(2, 2, 260, 16, (8, 8, 8, 8))
TITLE_BAR.circle(253, 10, 4)

TEXT_BOX = Polygon()
TEXT_BOX.rectangle(2, 30, 260, 125, (8, 8, 8, 8))

# Clear to white
display.set_pen(15)
display.clear()

display.set_font("bitmap8")
display.set_pen(0)
vector.draw(TITLE_BAR)
display.set_pen(15)
display.text("badgerOS", 7, 6, WIDTH, 1.0)
display.text("help", WIDTH - 40, 6, WIDTH, 1)

display.set_pen(2)
vector.draw(TEXT_BOX)

display.set_pen(1)
TEXT_SIZE = 2.0
y = 35 + int(LINE_HEIGHT / 2)
x = 5

display.set_font("bitmap8")
display.text("Up/Down - Move up and down", x, y, WIDTH, TEXT_SIZE)
y += LINE_HEIGHT
display.text("a - Move left", x, y, WIDTH, TEXT_SIZE)
y += LINE_HEIGHT
display.text("b - Launch selected app", x, y, WIDTH, TEXT_SIZE)
y += LINE_HEIGHT
display.text("c - Move right", x, y, WIDTH, TEXT_SIZE)
y += LINE_HEIGHT
display.text("a & c - Exit app", x, y, WIDTH, TEXT_SIZE)
y += LINE_HEIGHT

display.update()

# Call halt in a loop, on battery this switches off power.
# On USB, the app will exit when A+C is pressed because the launcher picks that up.
while True:
    # display.keepalive()  # TODO: No longer a problem because "halt" puts the board into powman sleep()
    display.halt()
