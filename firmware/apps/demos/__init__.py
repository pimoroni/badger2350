# Static demo browser for Badger's e-ink display: one demo per page, redrawn
# only on a button press (UP/DOWN to page, A/C to step, HOME to quit). Each
# demo's update(step) is called once to render a single frozen frame; there is
# no animation loop, so the step counter stands in for elapsed time.

import gc
import os
import sys

APP_DIR = "/system/apps/demos"

sys.path.insert(0, APP_DIR)
os.chdir(APP_DIR)

from demos import demos
names = sorted(demos.keys())

selected = 0
step = 0
demo = None
needs_render = True


def load_demo(index):
    global selected, demo, step
    # unload the previously running demo so re-entry re-runs its top-level setup
    if demo:
        del sys.modules[f"{APP_DIR}/demos/{names[selected]}"]
    gc.collect()
    selected = index % len(names)
    step = 0
    demo = __import__(demos[names[selected]])


def render():
    # demos assume a cleared white framebuffer and draw in black and grey.
    # Reset the settings demos opt into so a page looks the same however you
    # arrived at it.
    screen.pen = color.white
    screen.clear()
    screen.pen = color.black
    screen.font = font.sins
    screen.antialias = image.OFF
    screen.fill_rule = image.EVEN_ODD
    screen.alpha = 255

    try:
        demo.update(step)
    except Exception as e:  # noqa: BLE001 - a broken demo shouldn't kill the browser
        screen.pen = color.white
        screen.clear()
        screen.pen = color.black
        screen.text(f"{names[selected]}\n{e}", rect(4, 4, screen.width - 8, screen.height - 8))

    # demos that draw in colour set DITHER; the panel only has four grey levels
    # and picks them per channel, so unmapped colour washes out to white. Dither
    # before the caption so the caption itself stays crisp.
    if getattr(demo, "DITHER", False):
        screen.dither()

    # caption box (name, position, step), readable over any demo
    label = f"{names[selected]}  {selected + 1}/{len(names)}  #{step}"
    screen.font = font.sins
    screen.antialias = image.OFF
    screen.alpha = 255
    w, h = screen.measure_text(label)
    box = rect(2, screen.height - h - 6, w + 8, h + 5)
    screen.pen = color.white
    screen.shape(shape.rectangle(box.x, box.y, box.w, box.h))
    screen.pen = color.black
    screen.shape(shape.rectangle(box.x, box.y, box.w, box.h).stroke(1))
    screen.text(label, 6, screen.height - h - 4)

    # fast partial refresh for snappy page turns (first update is a full clear)
    badge.mode(FAST_UPDATE | NON_BLOCKING)
    badge.update()


def update():
    global needs_render, step

    if badge.pressed(BUTTON_DOWN):
        load_demo(selected + 1)
        needs_render = True
    elif badge.pressed(BUTTON_UP):
        load_demo(selected - 1)
        needs_render = True
    elif badge.pressed(BUTTON_C):
        step += 1
        needs_render = True
    elif badge.pressed(BUTTON_A):
        step = max(0, step - 1)
        needs_render = True

    if needs_render:
        render()
        needs_render = False

    wait_for_button_or_alarm()


load_demo(0)
run(update)
