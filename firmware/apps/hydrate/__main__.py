import badger_os
from picovector import ANTIALIAS_BEST, HALIGN_CENTER, PicoVector, Polygon, Transform

import badger2350
from badger2350 import HEIGHT, WIDTH

display = badger2350.Badger2350()
# display.led(0)
display.set_thickness(2)

# Pico Vector
vector = PicoVector(display.display)
vector.set_antialiasing(ANTIALIAS_BEST)
vector.set_font("Roboto-Medium-With-Material-Symbols.af", 20)
vector.set_font_align(HALIGN_CENTER)
t = Transform()

# Vector Elements
TITLE_BAR = Polygon()
TITLE_BAR.rectangle(2, 2, 260, 16, (8, 8, 8, 8))
TITLE_BAR.circle(253, 10, 4)
TEXT_BOX = Polygon()
TEXT_BOX.rectangle(2, 30, 260, 125, (8, 8, 8, 8))
BUTTON_BOX = Polygon()
BUTTON_BOX.rectangle(0, 0, 50, 20, (8, 8, 8, 8))

# Position of the buttons on the X axis
BUTTON_X_POS = [24, 104, 187]

# Centre point of the X axis
CENTRE_X = WIDTH // 2

# ------------------------------
#      User Settings
# ------------------------------
# Your daily goal and measurements
# Adjust these values to match your cup, bottle size or whatever suits you best :)
GOAL = 2000
WATER_MEASUREMENTS = [250, 500, 750]
MEASUREMENT_UNIT = "ml"

# Setup and load the state
state = {
    "goal": GOAL,
    "unit": MEASUREMENT_UNIT,
    "total": 0
}
badger_os.state_load("hydrate", state)

changed = False

woken_by_button = badger2350.woken_by_button()


def render():

    # display.led(128)

    # Clear to white
    display.set_pen(15)
    display.clear()

    # Draw our title bar
    display.set_font("bitmap8")
    display.set_pen(0)
    vector.draw(TITLE_BAR)
    display.set_pen(3)
    display.text("badgerOS", 7, 6, WIDTH, 1.0)
    display.text("Hydrate", WIDTH - 55, 6, WIDTH, 1)
    goal_width = display.measure_text(f"Goal: {GOAL}{MEASUREMENT_UNIT}", 1)
    goal_width //= 2
    display.text(f"Goal: {GOAL}{MEASUREMENT_UNIT}", CENTRE_X - goal_width, 6, WIDTH, 1)

    # Draw the 3 buttons and labels
    for i in range(3):
        display.set_pen(2)
        vector.set_transform(t)
        t.translate(BUTTON_X_POS[i], HEIGHT - 25)
        vector.draw(BUTTON_BOX)
        display.set_pen(0)
        measurement_string = f"{WATER_MEASUREMENTS[i]}{MEASUREMENT_UNIT}"
        measurement_offset = display.measure_text(measurement_string, 1)
        measurement_offset //= 2
        display.text(measurement_string, BUTTON_X_POS[i] + measurement_offset, HEIGHT - 18, WIDTH, 1)
        t.reset()

    # Draw the title
    vector.set_font_size(40)
    today_string = "Today:"
    today_offset = int(vector.measure_text(today_string)[2] // 2)
    vector.text(today_string, CENTRE_X - today_offset, 60)

    # Draw the current total
    vector.set_font_size(80)
    total_string = f"{state["total"]}{MEASUREMENT_UNIT}"
    total_offset = int(vector.measure_text(total_string)[2] // 2)
    vector.text(total_string, CENTRE_X - total_offset, 120)

    # Update the screen!
    display.update()
    # display.led(0)


def button(pin):
    global changed
    changed = True

    if pin == badger2350.BUTTON_A:
        state["total"] += WATER_MEASUREMENTS[0]

    if pin == badger2350.BUTTON_B:
        state["total"] += WATER_MEASUREMENTS[1]

    if pin == badger2350.BUTTON_C:
        state["total"] += WATER_MEASUREMENTS[2]

    # Press up to reset the total.
    if pin == badger2350.BUTTON_UP:
        state["total"] = 0

    if pin == badger2350.BUTTON_DOWN:
        pass

    if pin == badger2350.BUTTON_USER:
        pass


if not woken_by_button:
    changed = True

while True:

    # display.keepalive()  # TODO: No longer a problem because "halt" puts the board into powman sleep()

    if display.pressed(badger2350.BUTTON_A):
        button(badger2350.BUTTON_A)
    if display.pressed(badger2350.BUTTON_B):
        button(badger2350.BUTTON_B)
    if display.pressed(badger2350.BUTTON_C):
        button(badger2350.BUTTON_C)

    if display.pressed(badger2350.BUTTON_UP):
        button(badger2350.BUTTON_UP)
    if display.pressed(badger2350.BUTTON_DOWN):
        button(badger2350.BUTTON_DOWN)

    if changed:
        changed = False
        badger_os.state_save("hydrate", state)
        render()

    display.halt()
