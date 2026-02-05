import os
import sys
from badgeware import State


# Standalone bootstrap for finding app assets
os.chdir("/system/apps/mass_storage")

# Standalone bootstrap for module imports
sys.path.insert(0, "/system/apps/mass_storage")


# Called once to initialise your app.
def init():
    state = {
        "active": 0,
        "running": "/system/apps/menu"
    }
    State.load("menu", state)
    state["running"] = "/system/apps/menu"
    State.modify("menu", state)
    import _msc.py   # noqa F401


# Called every frame, update and render as you see fit!
def update():
    pass


# Handle saving your app state here
def on_exit():
    pass


# Standalone support for Thonny debugging
if __name__ == "__main__":
    run(update, init=init, on_exit=on_exit)
