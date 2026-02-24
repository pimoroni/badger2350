import os
import sys

sys.path.insert(0, "/system/apps/gallery")
os.chdir("/system/apps/gallery")

import ui

screen.font = rom_font.nope

files = []
total_files = len(os.listdir("/system/apps/gallery/images"))

# we don't want to continue if there are no images to show!
# we'll display an error and wait for the user to go back to the menu or enter disk mode
if total_files == 0:
    ui.draw_alert("No image files found.")
    while True:
        pass

bar_width = screen.width - 20
bar_x = (screen.width // 2) - (bar_width // 2)
segment_width = (bar_width // total_files)

state = {"index": 0,
         "ui_hidden": 0
         }

State.load("gallery", state)


def center_text(text, y):
    w, _ = screen.measure_text(text)
    screen.text(text, (screen.width / 2) - (w / 2), y)


# show loading screen
badge.mode(FAST_UPDATE | NON_BLOCKING)
ui.draw_alert("Loading...")

# Set the update speed back
badge.mode(MEDIUM_UPDATE | NON_BLOCKING)

# create a dictionary of all the images in the images directory
for file in os.listdir("/system/apps/gallery/images"):

    file = file.rsplit("/", 1)[-1]
    name, ext = file.rsplit(".", 1)
    if ext == "png":
        files.append({
            "name": file,
            "title": name.replace("-", " "),
            "image": image.load(f"/system/apps/gallery/images/{name}.png")
        })


# given a gallery image index it clamps it into the range of available images
def clamp_index(index):
    return index % len(files)


# load the main image based on the gallery index provided
def load_image(index):
    global image
    index = clamp_index(index)
    image = files[index]["image"]


# render the thumbnail strip
def draw_thumbnails():
    if state["ui_hidden"]:
        return

    w, h = 50, 36
    spacing = w + 10

    # draw the preview background
    screen.pen = color.white
    screen.rectangle(0, screen.height - 59, screen.width, 52)
    screen.pen = color.black
    screen.shape(shape.rectangle(-1, screen.height - 59, screen.width + 2, 52).stroke(1))
    
    # render the thumbnails
    for i in range(-3, 4):
        offset = state["index"] - int(state["index"])

        pos = (((i + -offset) * spacing) + (w * 2.2), screen.height - (h + 15))

        # determine which gallery image we're drawing the thumbnail for
        thumbnail = clamp_index(int(state["index"]) + i)
        thumbnail_image = files[thumbnail]["image"]

        # draw the active thumbnail outline
        if i == 0:
            screen.pen = color.black
            screen.shape(shape.rectangle(
                pos[0] - 2, pos[1] - 2, w + 4, h + 4))

        x, y, = pos
        screen.blit(thumbnail_image, rect(0, 0, thumbnail_image.width, thumbnail_image.height), rect(x, y, w, h))


# start up with the first image in the gallery
load_image(state["index"])


def update():
    global state

    badge.mode(MEDIUM_UPDATE | NON_BLOCKING)

    # if the user presses left or right then switch image
    if badge.pressed(BUTTON_A):
        state["index"] -= 1
        state["ui_hidden"] = False
        load_image(state["index"])

    if badge.pressed(BUTTON_C):
        state["index"] += 1
        state["ui_hidden"] = False
        load_image(state["index"])

    if badge.pressed(BUTTON_B):
        state["ui_hidden"] = not state["ui_hidden"]

    # draw the currently selected image
    screen.blit(image, rect(0, 0, image.width, image.height), rect(0, 0, screen.width, screen.height))

    # draw the thumbnail ui
    draw_thumbnails()

    screen.dither()

    title = files[clamp_index(state["index"])]["title"]
    width, _ = screen.measure_text(title)

    if not state["ui_hidden"]:
        badge.mode(FAST_UPDATE | NON_BLOCKING)
        screen.pen = color.white
        screen.shape(shape.rectangle(
            (screen.width / 2) - (width / 2) - 8, 1, width + 16, 17, 6))
        screen.pen = color.black
        screen.shape(shape.rectangle(
            (screen.width / 2) - (width / 2) - 8, 1, width + 16, 17, 6).stroke(1))
        screen.text(title, (screen.width / 2) - (width / 2), 3)

    badge.update()
    State.save("gallery", state)
    wait_for_button_or_alarm(timeout=10000)


run(update)
