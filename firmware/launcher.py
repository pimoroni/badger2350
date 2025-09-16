import gc
import math
import os
import time

import badger_os
from picovector import ANTIALIAS_BEST, HALIGN_CENTER, PicoVector, Polygon, Transform

import badger2350

changed = False
first_render = False
exited_to_launcher = False
woken_by_button = badger2350.woken_by_button()  # Must be done before we clear_pressed_to_wake


if badger2350.pressed_to_wake(badger2350.BUTTON_A) and badger2350.pressed_to_wake(badger2350.BUTTON_C):
    # Pressing A and C together at start quits app
    exited_to_launcher = badger_os.state_clear_running()
    badger2350.reset_pressed_to_wake()
else:
    # Otherwise restore previously running app
    badger_os.state_launch()


display = badger2350.Badger2350()
display.set_font("bitmap8")
# display.led(0)

BG = display.create_pen(195, 195, 195)

# Pico Vector
vector = PicoVector(display.display)
vector.set_antialiasing(ANTIALIAS_BEST)
t = Transform()
vector.set_font("Roboto-Medium-With-Material-Symbols.af", 20)
vector.set_font_align(HALIGN_CENTER)
vector.set_transform(t)

TITLE_BAR = Polygon()
TITLE_BAR.rectangle(2, 2, 260, 16, (8, 8, 8, 8))
TITLE_BAR.circle(253, 10, 4)

SELECTED_BORDER = Polygon()
SELECTED_BORDER.rectangle(0, 0, 90, 90, (10, 10, 10, 10), 5)

state = {
    "selected_file": "ebook/__main__",
    "running": "launcher"
}

badger_os.state_load("launcher", state)


class App:
    ICONS = {
        "badge": "\uea67",
        "book_2": "\uf53e",
        "cloud": "\ue2bd",
        "description": "\ue873",
        "help": "\ue887",
        "water_full": "\uf6d6",
        "wifi": "\ue63e",
        "image": "\ue3f4",
        "info": "\ue88e",
        "format_list_bulleted": "\ue241",
        "joystick": "\uf5ee"
    }
    DIRECTORY = "apps"
    DEFAULT_ICON = "description"
    ERROR_ICON = "help"  # TODO: have a reserved error icon

    def __init__(self, name):
        self._file = name
        self._meta = {
            "NAME": name,
            "ICON": App.DEFAULT_ICON,
            "DESC": ""
        }
        self.path = f"{name}/__main__"
        self._loaded = False

    def read_metadata(self):
        if self._loaded:
            return

        try:
            exec(open(f"{App.DIRECTORY}/{self._file}/__init__.py", "r").read(), self._meta)
        except SyntaxError:
            self._meta["ICON"] = App.ERROR_ICON
        self._loaded = True

    @property
    def name(self):
        self.read_metadata()
        return self._meta["NAME"]

    @property
    def icon(self):
        self.read_metadata()
        try:
            return App.ICONS[self._meta["ICON"]]
        except KeyError:
            return App.ICONS[App.ERROR_ICON]

    @property
    def desc(self):
        self.read_metadata()
        return self._meta["DESC"]

    @staticmethod
    def is_valid(file):
        try:
            open(f"{App.DIRECTORY}/{file}/__init__.py", "r")
            return True
        except OSError:
            return False



apps = [App(x) for x in os.listdir(App.DIRECTORY) if App.is_valid(x)]


# Page layout
centers = [[45, 52], [126, 52], [209, 52], [45, 130], [126, 130], [209, 130]]

MAX_PER_ROW = 3
MAX_PER_PAGE = MAX_PER_ROW * 2
ICONS_TOTAL = len(apps)
MAX_PAGE = math.ceil(ICONS_TOTAL / MAX_PER_PAGE)


def draw_disk_usage(x):
    _, f_used, _ = badger_os.get_disk_usage()

    display.set_pen(15)
    """
    display.image(
        bytearray(
            (
                0b00000000,
                0b00111100,
                0b00111100,
                0b00111100,
                0b00111000,
                0b00000000,
                0b00000000,
                0b00000001,
            )
        ),
        8,
        8,
        x,
        6,
    )
    """
    display.rectangle(x + 10, 5, 45, 10)
    display.set_pen(0)
    display.rectangle(x + 11, 6, 43, 8)
    display.set_pen(15)
    display.rectangle(x + 12, 7, int(41 / 100.0 * f_used), 6)


def render(selected_index):
    display.set_pen(BG)
    display.clear()
    display.set_pen(0)

    selected_page = selected_index // MAX_PER_PAGE

    icons = apps[selected_page * 6:selected_page * 6 + MAX_PER_PAGE]

    for index, app in enumerate(icons):
        x, y = centers[index]

        app.read_metadata()

        vector.set_font_size(20)
        vector.set_transform(t)
        vector.text(app.icon, x, y)
        t.translate(x, y)
        t.scale(0.8, 0.8)

        if selected_index % MAX_PER_PAGE == index:
            display.set_pen(1)
            t.translate(-45, -36)
            t.scale(1.0, 1.0)
            vector.draw(SELECTED_BORDER)
        t.reset()

        display.set_pen(0)
        vector.set_font_size(16)
        w = vector.measure_text(app.name)[2]
        vector.text(app.name, int(x - (w / 2)), y + 35)

    for i in range(MAX_PAGE):
        x = 253
        y = int((176 / 2) - (MAX_PAGE * 10 / 2) + (i * 10))
        display.set_pen(0)
        display.rectangle(x, y, 8, 8)
        if selected_page != i:
            display.set_pen(3)
            display.rectangle(x + 1, y + 1, 6, 6)

    display.set_pen(0)
    vector.draw(TITLE_BAR)

    draw_disk_usage(100)

    display.set_pen(3)
    vector.set_font_size(14)
    vector.text("BadgerOS", 7, 14)

    display.update()


def wait_for_user_to_release_buttons():
    while display.pressed_any():
        time.sleep(0.01)


def launch_example(file):
    wait_for_user_to_release_buttons()
    badger2350.reset_pressed_to_wake()

    file = f"{App.DIRECTORY}/{file}"

    for k in locals().keys():
        if k not in ("gc", "file", "badger_os"):
            del locals()[k]

    gc.collect()

    badger_os.launch(file)


def app_index(file):
    index = 0
    for app in apps:
        if app.path == file:
            break
        index += 1
    return index


selected_index = app_index(state["selected_file"])


if exited_to_launcher or not woken_by_button:
    wait_for_user_to_release_buttons()
    changed = True
    first_render = True


while True:
    # Sometimes a button press or hold will keep the system
    # powered *through* HALT, so latch the power back on.
    # display.keepalive()  # TODO: No longer a problem because "halt" puts the board into powman sleep

    if display.pressed(badger2350.BUTTON_A):
        if (selected_index % MAX_PER_ROW) > 0:
            selected_index -= 1
            changed = True

    if display.pressed(badger2350.BUTTON_B):
        launch_example(state["selected_file"])

    if display.pressed(badger2350.BUTTON_C):
        if (selected_index % MAX_PER_ROW) < MAX_PER_ROW - 1:
            selected_index += 1
            changed = True

    if display.pressed(badger2350.BUTTON_UP):
        if selected_index >= MAX_PER_ROW:
            selected_index -= MAX_PER_ROW
            changed = True

    if display.pressed(badger2350.BUTTON_DOWN):
        if selected_index < ICONS_TOTAL - 1:
            selected_index += MAX_PER_ROW
            selected_index = min(selected_index, ICONS_TOTAL - 1)
            changed = True

    if changed:
        state["selected_file"] = apps[selected_index].path
        badger_os.state_save("launcher", state)
        changed = False

        # If this is the first time we're calling render,
        # ie: cold boot, or exiting from an app
        # make sure it gets a good refresh
        if first_render:
            first_render = False
            display.set_update_speed(badger2350.UPDATE_MEDIUM)
        else:
            display.set_update_speed(badger2350.UPDATE_TURBO)

        render(selected_index)

    display.sleep()
