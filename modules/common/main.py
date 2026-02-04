import powman

if powman.get_wake_reason() == powman.WAKE_DOUBLETAP:
    import _msc  # noqa: F401


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
