import os
import sys

sys.path.insert(0, "/system/apps/menu")
sys.path.insert(0, "/")
os.chdir("/system/apps/menu")

import ui

from app import Apps

screen.font = rom_font.nope

badge.mode(FAST_UPDATE | NON_BLOCKING)

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

    apps.activate(state["active"])

    if changed:
        State.modify("menu", state)

    if badge.pressed(BUTTON_B):
        state["running"] = f"/system/apps/{apps.active.path}"
        State.modify("menu", state)
        # Reset into the newly running app
        reset()

    ui.draw_background()
    ui.draw_header()

    # draw menu apps
    apps.draw_icons()

    # draw label for active menu icon
    apps.draw_label()

    # Update the screen
    if changed or badge.first_update:
        badge.update()

    # Wait for a button press or alarm interrupt before continuing,
    # Sleep after 5 seconds if power is not connected.
    wait_for_button_or_alarm(timeout=5000)


run(update)
