import time

import badgeware


def hold():
    badgeware.message("Connected", "The Badgeware IDE is updating files.\n\nPress any button to cancel.")
    display.update()


def safe_mode():
    badgeware.message("Safe Mode", "Connect to the Badgeware IDE to repair your badge.\n\nPress RESET to restart.")
    display.update()


def error(_title, _message):
    while display.busy():
        time.sleep_ms(10)
