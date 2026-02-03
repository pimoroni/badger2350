import os
import sys

sys.path.insert(0, "/system/apps/menu")
sys.path.insert(0, "/")
os.chdir("/system/apps/menu")

import ui
from badgeware import run, State

from app import Apps

screen.font = rom_font.nope

mode(FAST_UPDATE)

# find installed apps and create apps
apps = Apps("/system/apps")

state = {
    "active": 0,
    "running": "/system/apps/menu"
}
State.load("menu", state)

# If the initial state is out of range, revert to index 0
if state["active"] >= len(apps):
    state["active"] = 0
    State.modify("menu", state)


def update():
    global active, apps

    # process button inputs to switch between apps
    if io.BUTTON_C in io.pressed:
        if (state["active"] % 3) < 2 and state["active"] < len(apps) - 1:
            state["active"] += 1
    if io.BUTTON_A in io.pressed:
        if (state["active"] % 3) > 0 and state["active"] > 0:
            state["active"] -= 1
    if io.BUTTON_UP in io.pressed and state["active"] >= 3:
        state["active"] -= 3
    if io.BUTTON_DOWN in io.pressed:
        state["active"] += 3
        if state["active"] >= len(apps):
            state["active"] = len(apps) - 1

    apps.activate(state["active"])

    State.modify("menu", state)

    if io.BUTTON_B in io.pressed:
        state["running"] = f"/system/apps/{apps.active.path}"
        State.modify("menu", state)
        while io.BUTTON_B in io.pressed or io.BUTTON_B in io.held:
            io.poll()
        return state["running"]

    ui.draw_background()
    ui.draw_header()

    # draw menu apps
    apps.draw_icons()

    # draw label for active menu icon
    apps.draw_label()

    return None


if __name__ == "__main__":
    run(update)
