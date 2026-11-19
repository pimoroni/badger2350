import ide
import powman

ide.serve()

if powman.get_wake_reason() == powman.WAKE_DOUBLETAP:
    ide.safe_mode()

else:
    try:
        with open("hardware_test.txt", "r"):
            import hardware_test   # noqa F401
    except OSError:
        pass

    if not file_exists("/apps/menu/__init__.py"):
        fatal_error("System Error!", "Could not find the launcher in /apps/menu. Connect to the Badgeware IDE to reinstall it!")

    state = {
        "active": 0,
        "running": "/apps/menu"
    }
    State.load("menu", state)

    app = state["running"]

    if not file_exists(app) or powman.get_wake_reason() == powman.WAKE_RESET:
        app = state["running"] = "/apps/menu"
        State.modify("menu", state)
        rtc.clear_alarm()

    launch(app)

    state["running"] = "/apps/menu"
    State.modify("menu", state)
    rtc.clear_alarm()

    reset()
