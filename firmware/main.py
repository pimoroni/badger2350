import machine
import powman

state = {
    "active": 0,
    "running": "/system/apps/menu"
}
State.load("menu", state)

app = state["running"]

# Trying to launch an app that has been removed, or "reset" has been pressed
if not file_exists(app) or powman.get_wake_reason() == powman.WAKE_RESET:
    app = state["running"] = "/system/apps/menu"
    State.modify("menu", state)

launch(app)

state["running"] = "/system/apps/menu"
State.modify("menu", state)

machine.reset()
