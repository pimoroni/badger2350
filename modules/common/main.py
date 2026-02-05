import os
import powman
from badgeware import fatal_error

if powman.get_wake_reason() == powman.WAKE_DOUBLETAP:
    import _msc  # noqa: F401


try:
    os.listdir("/system")
except OSError:
    fatal_error("System Error!", "Unable to mount filesystem. This may be a temporary error, try resetting your board again.")


try:
    with open("hardware_test.txt", "r"):
        import hardware_test   # noqa F401
except OSError:
    pass

try:
    __import__("/main")
except ImportError:
    try:
        __import__("/system/main")
    except ImportError:
        import _error  # noqa: F401
