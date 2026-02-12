import machine

state = {
    "active": 0,
    "running": "/system/apps/menu"
}
State.load("menu", state)

app = state["running"]

# Trying to launch an app that has been removed
if not file_exists(app):
    state["running"] = "/system/apps/menu"
    State.modify("menu", state)
    app = state["running"]

run(app)

machine.reset()
