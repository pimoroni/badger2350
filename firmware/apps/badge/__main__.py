import jpegdec
import pngdec
from picovector import ANTIALIAS_BEST, HALIGN_CENTER, PicoVector, Polygon, Transform

import badger2350

# Global Constants
WIDTH = badger2350.WIDTH
HEIGHT = badger2350.HEIGHT

COMPANY_TEXT_SIZE = 0.6
DETAILS_TEXT_SIZE = 0.5

CENTRE_X = WIDTH // 2
CENTRE_Y = HEIGHT // 2

BADGE_PATH = "/badges/badge.txt"

DEFAULT_TEXT = """mustelid inc
H. Badger
RP2350
16MB Flash
/badges/badger-mugshot.png
"""


# ------------------------------
#      Drawing functions
# ------------------------------

# Draw the badge, including user text
def draw_badge():
    display.set_pen(BG)
    display.clear()

    # Draw background logo on the right side.
    display.set_pen(2)
    vector.set_font_size(80)
    vector.text("\uea4b", WIDTH - 20, CENTRE_Y)

    # Draw the left side background shapes
    shapes = [Polygon(), Polygon()]
    shapes[0].regular(0, 0, 145, 3)
    shapes[1].regular(0, 0, 120, 3)

    t.translate(50, HEIGHT)
    t.rotate(180, (0, 0))
    vector.draw(shapes[0])
    t.reset()
    display.set_pen(1)
    vector.draw(shapes[1])

    # Set the text font
    display.set_pen(1)

    # draw name
    vector.set_font_size(40)
    vector.text(name, 10, CENTRE_Y + 45)

    # draw title
    vector.set_font_size(15)
    vector.text(title, 10, CENTRE_Y + 60)

    # draw additional line
    vector.set_font_size(15)
    vector.text(additional_text, 10, CENTRE_Y + 75)

    try:
        # Draw badge image
        png.open_file(badge_image)
        png.decode(10, 10)
    except (OSError, RuntimeError):
        # Draw badge image
        jpeg.open_file(badge_image)
        jpeg.decode(10, 10)

    display.update()


# ------------------------------
#        Program setup
# ------------------------------

# Create a new Badger and set it to update NORMAL
display = badger2350.Badger2350()
# display.led(0)
display.set_update_speed(badger2350.UPDATE_NORMAL)

BG = display.create_pen(195, 195, 195)

jpeg = jpegdec.JPEG(display.display)
png = pngdec.PNG(display.display)

# Pico Vector
vector = PicoVector(display.display)
vector.set_antialiasing(ANTIALIAS_BEST)
vector.set_font("Roboto-Medium-With-Material-Symbols.af", 20)
vector.set_font_align(HALIGN_CENTER)
t = Transform()
vector.set_transform(t)

BACKGROUND_RECT = Polygon()
BACKGROUND_RECT.rectangle(0, 0, WIDTH, HEIGHT)
BACKGROUND_RECT.rectangle(WIDTH - 90, 10, 80, 80, (8, 8, 8, 8))

# Open the badge file
try:
    badge = open(BADGE_PATH, "r")
except OSError:
    with open(BADGE_PATH, "w") as f:
        f.write(DEFAULT_TEXT)
        f.flush()
    badge = open(BADGE_PATH, "r")

# Read in the next 6 lines
company = badge.readline()        # "mustelid inc"
name = badge.readline()           # "H. Badger"
title = badge.readline()  # "RP2040"
additional_text = badge.readline()   # "2MB Flash"
badge_image = badge.readline()    # /badges/badge.jpg

# ------------------------------
#       Main program
# ------------------------------

draw_badge()

while True:
    # Sometimes a button press or hold will keep the system
    # powered *through* HALT, so latch the power back on.
    # display.keepalive()  # TODO: No longer a problem because "halt" puts the board into powman sleep()

    # If on battery, halt the Badger to save power, it will wake up if any of the front buttons are pressed
    display.halt()
