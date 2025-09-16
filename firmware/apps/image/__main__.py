import os

import badger_os
import jpegdec
import pngdec
from picovector import ANTIALIAS_BEST, PicoVector, Polygon, Transform

import badger2350
from badger2350 import HEIGHT, WIDTH

TOTAL_IMAGES = 0


# Turn the act LED on as soon as possible
display = badger2350.Badger2350()
# display.led(128)
display.set_update_speed(badger2350.UPDATE_NORMAL)

jpeg = jpegdec.JPEG(display.display)
png = pngdec.PNG(display.display)

# Pico Vector
vector = PicoVector(display.display)
vector.set_antialiasing(ANTIALIAS_BEST)
t = Transform()


# Load images
try:
    IMAGES = [f for f in os.listdir("/images") if f.endswith((".jpg", ".png"))]
    TOTAL_IMAGES = len(IMAGES)
except OSError:
    pass


state = {
    "current_image": 0,
    "show_info": True
}


def show_image(n):
    file = IMAGES[n]
    name, ext = file.split(".")

    try:
        png.open_file("/images/{}".format(file))
        png.decode()
    except (OSError, RuntimeError):
        jpeg.open_file("/images/{}".format(file))
        jpeg.decode()

    if state["show_info"]:

        label = f"{name} ({ext})"
        name_length = display.measure_text(label, 0.5)
        display.set_pen(3)
        text_box = Polygon().rectangle(2, HEIGHT - 23, name_length + 11, 21, (10, 10, 10, 10))
        vector.draw(text_box)
        display.set_pen(0)
        display.text(label, 7, HEIGHT - 15, WIDTH, 0.5)

        for i in range(TOTAL_IMAGES):
            x = WIDTH - 10
            y = int((HEIGHT / 2) - (TOTAL_IMAGES * 10 / 2) + (i * 10))
            display.set_pen(1)
            display.rectangle(x, y, 8, 8)
            if state["current_image"] != i:
                display.set_pen(2)
                display.rectangle(x + 1, y + 1, 6, 6)

    display.update()


if TOTAL_IMAGES == 0:
    raise RuntimeError("To run this demo, create an /images directory on your device and upload some 1bit 264x176 pixel images.")


badger_os.state_load("image", state)

changed = True


while True:
    # Sometimes a button press or hold will keep the system
    # powered *through* HALT, so latch the power back on.
    # display.keepalive()  # TODO: No longer a problem because "halt" puts the board into powman sleep()

    if display.pressed(badger2350.BUTTON_UP):
        if state["current_image"] > 0:
            state["current_image"] -= 1
            changed = True

    if display.pressed(badger2350.BUTTON_DOWN):
        if state["current_image"] < TOTAL_IMAGES - 1:
            state["current_image"] += 1
            changed = True

    if display.pressed(badger2350.BUTTON_A):
        state["show_info"] = not state["show_info"]
        changed = True

    if changed:
        show_image(state["current_image"])
        badger_os.state_save("image", state)
        changed = False

    # Halt the Badger to save power, it will wake up if any of the front buttons are pressed
    display.halt()
