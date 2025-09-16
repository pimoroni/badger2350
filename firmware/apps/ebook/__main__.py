
import gc

import badger_os
from picovector import ANTIALIAS_BEST, PicoVector, Polygon, Transform

import badger2350

# **** Put the name of your text file here *****
text_file = "/books/289-0-wind-in-the-willows-abridged.txt"  # File must be on the MicroPython device

gc.collect()

# Global Constants
WIDTH = badger2350.WIDTH
HEIGHT = badger2350.HEIGHT

ARROW_WIDTH = 18

TEXT_PADDING = 4
TEXT_WIDTH = WIDTH - TEXT_PADDING - TEXT_PADDING - ARROW_WIDTH

FONTS = ["sans", "gothic", "cursive", "serif"]
THICKNESSES = [2, 1, 1, 2]

CHEVRON = [[(3.0, -10.0), (-12.33, -25.33), (-7.67, -30.0), (12.33, -10.0),
            (-7.67, 10.0), (-12.33, 5.33), (3.0, -10.0)]]

TITLE_BAR = Polygon()
TITLE_BAR.rectangle(2, 2, 260, 16, (8, 8, 8, 8))
TITLE_BAR.circle(253, 10, 4)

V_BAR = Polygon()
V_BAR.rectangle(WIDTH - 18, 25, 17, 125, (8, 8, 8, 8))

arrow = Polygon()

for path in CHEVRON:
    arrow.path(*path)

# ------------------------------
#      Drawing functions
# ------------------------------


# Draw arrow at X and Y position and rotate
def draw_arrow(pos_x, pos_y, rotate=0):

    t.translate(pos_x, pos_y)
    t.scale(0.34, 0.34)
    t.rotate(rotate, rotate)
    vector.draw(arrow)
    t.reset()


# Draw the frame of the reader
def draw_frame():
    display.set_pen(15)
    display.clear()
    display.set_pen(2)
    vector.draw(V_BAR)
    display.set_pen(0)
    if state["current_page"] > 0:
        draw_arrow(WIDTH - 6, (HEIGHT // 4), -90)

    draw_arrow(WIDTH - 13, HEIGHT - (HEIGHT // 4), 89)

    display.set_font("bitmap8")
    display.set_thickness(0)
    display.set_pen(0)
    vector.draw(TITLE_BAR)
    display.set_pen(3)
    display.text(f"{text_file[:30]}...", 7, 6, WIDTH, 1)
    display.text("eBook", WIDTH - 45, 6, WIDTH, 1)

# ------------------------------
#        Program setup
# ------------------------------


# Global variables
state = {
    "last_offset": 0,
    "current_page": 0,
    "font_idx": 0,
    "text_size": 0.5,
    "offsets": []
}
badger_os.state_load("ebook", state)

text_spacing = int(34 * state["text_size"])


# Create a new Badger and set it to update FAST
display = badger2350.Badger2350()
# display.led(128)
display.set_update_speed(badger2350.UPDATE_FAST)

# Pico Vector
vector = PicoVector(display.display)
vector.set_antialiasing(ANTIALIAS_BEST)
t = Transform()
vector.set_transform(t)


# ------------------------------
#         Render page
# ------------------------------

def render_page():
    row = 1
    line = ""
    pos = ebook.tell()
    next_pos = pos
    add_newline = False
    display.set_font(FONTS[state["font_idx"]])
    display.set_thickness(THICKNESSES[state["font_idx"]])

    while True:
        # Read a full line and split it into words
        words = ebook.readline().split(" ")

        # Take the length of the first word and advance our position
        next_word = words[0]
        if len(words) > 1:
            next_pos += len(next_word) + 1
        else:
            next_pos += len(next_word)  # This is the last word on the line

        # Advance our position further if the word contains special characters
        if "\u201c" in next_word:
            next_word = next_word.replace("\u201c", '"')
            next_pos += 2
        if "\u201d" in next_word:
            next_word = next_word.replace("\u201d", '"')
            next_pos += 2
        if "\u2019" in next_word:
            next_word = next_word.replace("\u2019", "'")
            next_pos += 2

        # Rewind the file back from the line end to the start of the next word
        ebook.seek(next_pos)

        # Strip out any new line characters from the word
        next_word = next_word.strip()

        # If an empty word is encountered assume that means there was a blank line
        if len(next_word) == 0:
            add_newline = True

        # Append the word to the current line and measure its length
        appended_line = line
        if len(line) > 0 and len(next_word) > 0:
            appended_line += " "
        appended_line += next_word
        appended_length = display.measure_text(appended_line, state["text_size"])

        # Would this appended line be longer than the text display area, or was a blank line spotted?
        if appended_length >= TEXT_WIDTH or add_newline:

            # Yes, so write out the line prior to the append
            print(line)
            display.set_pen(0)
            display.text(line, TEXT_PADDING, (row * text_spacing) + (text_spacing // 2) + TEXT_PADDING, WIDTH, state["text_size"])

            # Clear the line and move on to the next row
            line = ""
            row += 1

            # Have we reached the end of the page?
            if (row * text_spacing) + text_spacing >= HEIGHT:
                print("+++++")
                display.update()

                # Reset the position to the start of the word that made this line too long
                ebook.seek(pos)
                return
            # Set the line to the word and advance the current position
            line = next_word
            pos = next_pos

            # A new line was spotted, so advance a row
            if add_newline:
                print("")
                row += 1
                if (row * text_spacing) + text_spacing >= HEIGHT:
                    print("+++++")
                    display.update()
                    return
                add_newline = False
        else:
            # The appended line was not too long, so set it as the line and advance the current position
            line = appended_line
            pos = next_pos


# ------------------------------
#       Main program loop
# ------------------------------

launch = True
changed = False

# Open the book file
ebook = open(text_file, "r")
if len(state["offsets"]) > state["current_page"]:
    ebook.seek(state["offsets"][state["current_page"]])
else:
    state["current_page"] = 0
    state["offsets"] = []

while True:
    # Sometimes a button press or hold will keep the system
    # powered *through* HALT, so latch the power back on.
    # display.keepalive()  # TODO: No longer a problem because "halt" puts the board into powman sleep()

    # Was the next page button pressed?
    if display.pressed(badger2350.BUTTON_DOWN):
        state["current_page"] += 1

        changed = True

    # Was the previous page button pressed?
    if display.pressed(badger2350.BUTTON_UP):
        if state["current_page"] > 0:
            state["current_page"] -= 1
            if state["current_page"] == 0:
                ebook.seek(0)
            else:
                ebook.seek(state["offsets"][state["current_page"] - 1])  # Retrieve the start position of the last page
            changed = True

    if display.pressed(badger2350.BUTTON_A):
        state["text_size"] += 0.1
        if state["text_size"] > 0.8:
            state["text_size"] = 0.5
        text_spacing = int(34 * state["text_size"])
        state["offsets"] = []
        ebook.seek(0)
        state["current_page"] = 0
        changed = True

    if display.pressed(badger2350.BUTTON_B):
        state["font_idx"] += 1
        if (state["font_idx"] >= len(FONTS)):
            state["font_idx"] = 0
        state["offsets"] = []
        ebook.seek(0)
        state["current_page"] = 0
        changed = True

    if launch and not changed:
        if state["current_page"] > 0 and len(state["offsets"]) > state["current_page"] - 1:
            ebook.seek(state["offsets"][state["current_page"] - 1])
        changed = True
        launch = False

    if changed:
        draw_frame()
        render_page()

        # Is the next page one we've not displayed before?
        if state["current_page"] >= len(state["offsets"]):
            state["offsets"].append(ebook.tell())  # Add its start position to the state["offsets"] list
        badger_os.state_save("ebook", state)

        changed = False

    display.halt()
