import os
import sys

from badgeware import State, run

sys.path.insert(0, "/system/apps/list")
os.chdir("/system/apps/list")

import binascii

# **** Put your list title here *****
list_title = "Checklist"
list_file = "checklist.txt"


# Global Constants
WIDTH = screen.width
HEIGHT = screen.height

ARROW_WIDTH = 14
ARROW_HEIGHT = 14

ITEM_SPACING = 25

LIST_START = 36
LIST_PADDING = 3
LIST_WIDTH = WIDTH - LIST_PADDING - LIST_PADDING - ARROW_WIDTH
LIST_HEIGHT = HEIGHT - LIST_START - LIST_PADDING - ARROW_HEIGHT

# Default list items
# Create your own list and save it as "checklist.txt" in the list app folder :)
list_items = ["Badger", "Badger", "Badger", "Badger", "Badger", "Mushroom", "Mushroom", "Snake"]

ICONS = {"up": image.load("assets/arrow_up.png"),
         "down": image.load("assets/arrow_down.png"),
         "left": image.load("assets/arrow_left.png"),
         "right": image.load("assets/arrow_right.png"),
         "check": image.load("assets/check.png"),
         "cross": image.load("assets/cross.png")}

try:
    with open("checklist.txt", "r") as f:
        raw_list_items = f.read()

    if raw_list_items.find(" X\n") != -1:
        # Have old style checklist, preserve state and note we should resave the list to remove the Xs
        list_items = []
        state = {
            "current_item": 0,
            "checked": []
        }
        for item in raw_list_items.strip().split("\n"):
            if item.endswith(" X"):
                state["checked"].append(True)
                item = item[:-2]
            else:
                state["checked"].append(False)
            list_items.append(item)
        state["items_hash"] = binascii.crc32("\n".join(list_items))

        State.save("list", state)
    else:
        list_items = [item.strip() for item in raw_list_items.strip().split("\n")]

except OSError:
    State.delete("list")


# Draw the list of items
def draw_list(items, item_states, start_item, highlighted_item, x, y, width, height, item_height, columns):
    item_x = 5
    item_y = 0
    current_col = 0
    screen.pen = color.black
    for i in range(start_item, len(items)):
        if i == highlighted_item:
            screen.shape(shape.rectangle(item_x, item_y + y - (item_height // 2), (width // columns) - 1, item_height - 2).stroke(1))
        screen.text(items[i], item_x + x + item_height, item_y + y - 7)
        draw_checkbox(item_x, item_y + y - (item_height // 2), item_height, color.black, 1, item_states[i], 2)
        item_y += item_height
        if item_y >= height - (item_height // 2):
            item_x += width // columns
            item_y = 0
            current_col += 1
            if current_col >= columns:
                return


# Draw a checkbox with or without a tick
def draw_checkbox(x, y, size, color, thickness, tick, padding):
    border = (thickness // 2) + padding

    if tick:
        screen.blit(ICONS["check"], vec2(x + 5, y + 4))

    screen.pen = color
    screen.shape(shape.rectangle(x, y, size - border, size - border).stroke(thickness))


def draw_header():
    # create animated header text
    w, _ = screen.measure_text(list_title)
    pos = ((screen.width / 2) - (w / 2), 1)

    screen.pen = color.white
    screen.shape(shape.rectangle(0, 0, screen.width, 15))

    screen.pen = color.black
    screen.line(4, 4, screen.width - 4, 4)
    screen.line(4, 6, screen.width - 4, 6)
    screen.line(4, 8, screen.width - 4, 8)
    screen.line(4, 10, screen.width - 4, 10)
    screen.line(0, 15, screen.width, 15)

    screen.pen = color.white
    screen.shape(shape.rectangle(pos[0] - 5, 0, w + 10, 15))

    screen.pen = color.black
    screen.text(list_title, *pos)


changed = True
state = {
    "current_item": 0,
}
State.load("list", state)
items_hash = binascii.crc32("\n".join(list_items))
if "items_hash" not in state or state["items_hash"] != items_hash:
    # Item list changed, or not yet written reset the list
    state["current_item"] = 0
    state["items_hash"] = items_hash
    state["checked"] = [False] * len(list_items)
    changed = True

# Global variables
items_per_page = 0

# Find out what the longest item is
longest_item = 0
for i in range(len(list_items)):
    while True:
        item = list_items[i]
        item_length, _ = screen.measure_text(item)
        if item_length > 0 and item_length > LIST_WIDTH - ITEM_SPACING:
            list_items[i] = item[:-1]
        else:
            break
    longest_item = max(longest_item, screen.measure_text(list_items[i])[0])


# And use that to calculate the number of columns we can fit onscreen and how many items that would give
list_columns = 1
while longest_item + ITEM_SPACING < (LIST_WIDTH // (list_columns + 1)):
    list_columns += 1

items_per_page = ((LIST_HEIGHT // ITEM_SPACING) + 1) * list_columns


def center_text(text, y):
    w, _ = screen.measure_text(text)
    screen.text(text, (screen.width / 2) - (w / 2), y)


def update():
    global changed

    badge.mode(FAST_UPDATE)
    if len(list_items) > 0:
        if badge.pressed(BUTTON_A):
            if state["current_item"] > 0:
                state["current_item"] = max(state["current_item"] - (items_per_page) // list_columns, 0)
                changed = True
        if badge.pressed(BUTTON_B):
            state["checked"][state["current_item"]] = not state["checked"][state["current_item"]]
            badge.mode(MEDIUM_UPDATE)
            changed = True
        if badge.pressed(BUTTON_C):
            if state["current_item"] < len(list_items) - 1:
                state["current_item"] = min(state["current_item"] + (items_per_page) // list_columns, len(list_items) - 1)
                changed = True
        if badge.pressed(BUTTON_UP):
            if state["current_item"] > 0:
                state["current_item"] -= 1
                changed = True
        if badge.pressed(BUTTON_DOWN):
            if state["current_item"] < len(list_items) - 1:
                state["current_item"] += 1
                changed = True

    if changed:
        State.save("list", state)
        changed = False

    screen.pen = color.white
    screen.clear()

    draw_header()

    screen.pen = brush.pattern(color.white, color.dark_grey, 21)
    screen.shape(shape.rectangle(WIDTH - ARROW_WIDTH - 1, 15, ARROW_WIDTH + 2, HEIGHT))
    screen.shape(shape.rectangle(0, HEIGHT - ARROW_HEIGHT - 2, WIDTH, ARROW_HEIGHT + 2))

    screen.pen = color.black
    screen.shape(shape.rectangle(WIDTH - ARROW_WIDTH - 1, 15, ARROW_WIDTH + 2, HEIGHT).stroke(1))
    screen.shape(shape.rectangle(0, HEIGHT - ARROW_HEIGHT - 2, WIDTH, ARROW_HEIGHT + 2).stroke(1))

    y = LIST_PADDING
    y += 12

    if len(list_items) > 0:
        page_item = 0
        if items_per_page > 0:
            page_item = (state["current_item"] // items_per_page) * items_per_page

        # Draw the list
        draw_list(list_items, state["checked"], page_item, state["current_item"], LIST_PADDING, LIST_START,
                  LIST_WIDTH, LIST_HEIGHT, ITEM_SPACING, list_columns)

        # Previous item
        if state["current_item"] > 0:
            screen.pen = color.white
            screen.blit(ICONS["up"], rect(WIDTH - ARROW_WIDTH, ARROW_HEIGHT + 2,
                        ARROW_WIDTH, ARROW_HEIGHT))

        # Next item
        if state["current_item"] < (len(list_items) - 1):
            screen.pen = color.white
            screen.blit(ICONS["down"], rect(WIDTH - ARROW_WIDTH, HEIGHT - 30,
                        ARROW_WIDTH, ARROW_HEIGHT))

        # Previous column
        if state["current_item"] > 0:
            screen.blit(ICONS["left"], rect(2, HEIGHT - ARROW_HEIGHT - 1,
                        ARROW_WIDTH, ARROW_HEIGHT))

        # Next column
        if state["current_item"] < (len(list_items) - 1):
            screen.blit(ICONS["right"], rect(WIDTH - (ARROW_WIDTH * 2) - 2, HEIGHT - ARROW_HEIGHT - 1,
                        ARROW_WIDTH, ARROW_HEIGHT))

        if state["checked"][state["current_item"]]:
            # Tick off item
            screen.blit(ICONS["cross"], rect((WIDTH // 2) - (ARROW_WIDTH // 2), HEIGHT - ARROW_HEIGHT - 1,
                        ARROW_HEIGHT, ARROW_HEIGHT))
        else:
            # Untick item
            screen.blit(ICONS["check"], rect((WIDTH // 2) - (ARROW_WIDTH // 2), HEIGHT - ARROW_HEIGHT - 1,
                        ARROW_HEIGHT, ARROW_HEIGHT))
    else:
        # Say that the list is empty
        empty_text = "Nothing Here"
        text_length = display.measure_text(empty_text)
        screen.text(empty_text, ((LIST_PADDING + LIST_WIDTH) - text_length) // 2, (LIST_HEIGHT // 2) + LIST_START - (ITEM_SPACING // 4))


def on_exit():
    pass


if __name__ == "__main__":
    run(update)
