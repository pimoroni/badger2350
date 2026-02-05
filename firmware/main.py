# This file is copied from /system/main.py to /main.py on first run

import os
import sys

import machine
from badgeware import State


def quit_to_launcher(pin):
    global running_app

    state["running"] = "/system/apps/menu"
    State.modify("menu", state)

    getattr(running_app, "on_exit", lambda: None)()
    # If we reset while boot is low, bad times
    while not pin.value():
        pass
    machine.reset()


state = {
    "active": 0,
    "running": "/system/apps/menu"
}
State.load("menu", state)

app = state["running"]

machine.Pin.board.BUTTON_HOME.irq(
    trigger=machine.Pin.IRQ_FALLING, handler=quit_to_launcher
)


# Trying to launch an app that has been removed
if not file_exists(app):
    state["running"] = "/system/apps/menu"
    State.modify("menu", state)
    app = state["running"]


sys.path.insert(0, app)
try:
    os.chdir(app)
    running_app = __import__(app)
    getattr(running_app, "init", lambda: None)()
except Exception as e:  # noqa: BLE001
    fatal_error("Error!", e)

run(running_app.update)

machine.reset()
