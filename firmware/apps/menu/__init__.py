import os
import sys

sys.path.insert(0, "/system/apps/menu")
sys.path.insert(0, "/")
os.chdir("/system/apps/menu")

import ui
from badgeware import State

from app import Apps

screen.font = rom_font.nope

badge.mode(FAST_UPDATE)

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
    global apps

    active = state["active"]

    # process button inputs to switch between apps
    if badge.pressed(BUTTON_C):
        if (state["active"] % 3) < 2 and state["active"] < len(apps) - 1:
            state["active"] += 1
    if badge.pressed(BUTTON_A):
        if (state["active"] % 3) > 0 and state["active"] > 0:
            state["active"] -= 1
    if badge.pressed(BUTTON_UP) and state["active"] >= 3:
        state["active"] -= 3
    if badge.pressed(BUTTON_DOWN):
        state["active"] += 3
        if state["active"] >= len(apps):
            state["active"] = len(apps) - 1

    changed = state["active"] != active

    # If the state hasn't changed ad we're not handling
    # the initial display refresh, do not refresh the screen
    if not changed and not badge.first_update:
        return False

    apps.activate(state["active"])

    if changed:
        State.modify("menu", state)

    if badge.pressed(BUTTON_B):
        state["running"] = f"/system/apps/{apps.active.path}"
        State.modify("menu", state)
        while badge.pressed(BUTTON_B) or badge.held(BUTTON_B):
            badge.poll()
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
