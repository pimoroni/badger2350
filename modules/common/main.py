import powman
from badgeware import message


def safe_mode():
    message("Safe Mode", "Connect to the Badgeware IDE to repair your badge.\n\nPress RESET to restart.")
    display.update()


if powman.get_wake_reason() == powman.WAKE_DOUBLETAP:
    safe_mode()

else:
    try:
        with open("hardware_test.txt", "r"):
            import hardware_test   # noqa F401
    except OSError:
        pass

    try:
        __import__("/system/main")
    except ImportError:
        fatal_error("System Error!", "Could not find /system/main.py. Connect to the Badgeware IDE to reinstall it!")
