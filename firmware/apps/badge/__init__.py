import sys
import os

sys.path.insert(0, "/system/apps/badge")
os.chdir("/system/apps/badge")


CX = screen.width / 2
CY = screen.height / 2

screen.antialias = screen.X2

# details to be shown on the card
id_photo = image.load("avatar.png")
id_name = "Your Name"
id_role = "Job title"

# see the 'assets/social' folder to see what's supported
id_socials = {"bluesky": {"icon": None, "handle": "@bluesky"},
              "instagram": {"icon": None, "handle": "@instagram"},
              "github": {"icon": None, "handle": "@github"},
              "discord": {"icon": None, "handle": "@discord"}
              }

# load in the social icons
for key in id_socials.keys():
    id_socials[key]["icon"] = image.load(f"assets/socials/{key}.png")

# id card variables
id_body = shape.rectangle(0, 0, 240, 155 )
id_outline = shape.rectangle(0, 0, 240, 155).stroke(2)
background = brush.pattern(color.black, color.white, 6)
rear_view = False
card_pos = (10, 10)
pattern = 25

small_font = rom_font.smart
large_font = rom_font.ignore


def center_text(text, y):
    w, _ = screen.measure_text(text)
    screen.text(text, (screen.width / 2) - (w / 2), y)


def init():
    pass


def update():
    global rear_view, background, pattern

    # unpack the x and y for the card
    x, y = card_pos

    # clear the screen
    screen.pen = brush.pattern(color.white, color.black, pattern)
    screen.clear()

    if badge.pressed(BUTTON_B):
        rear_view = not rear_view

    if badge.pressed(BUTTON_UP):
        pattern += 1

    if badge.pressed(BUTTON_DOWN):
        pattern -= 1

    pattern = clamp(pattern, 0, 37)

    # draw the card
    id_body.transform = mat3().translate(CX, y)
    id_outline.transform = mat3().translate(CX, y)
    id_body.transform = id_body.transform.translate(-120, 0)
    id_outline.transform = id_outline.transform.translate(-120, 0)

    screen.pen = color.dark_grey
    id_body.transform = id_body.transform.translate(4, 4)
    screen.shape(id_body)

    screen.pen = color.white
    id_body.transform = id_body.transform.translate(-4, -4)
    screen.shape(id_body)
    screen.pen = color.black
    screen.shape(id_outline)

    photo_y = y + 18 + id_photo.height
    socials_y = 32

    # Draw the card information
    screen.pen = color.black
    if not rear_view:
        screen.font = large_font
        screen.blit(id_photo, vec2(CX - id_photo.width / 2, y + 15))
        center_text(id_name, photo_y)
        screen.font = small_font
        center_text(id_role, photo_y + 31)
    else:
        screen.pen = color.black
        screen.font = small_font
        for account in id_socials.items():
            screen.blit(account[1]["icon"], vec2(30, socials_y))
            screen.text(account[1]["handle"], 55, socials_y)
            socials_y += 31


def on_exit():
    pass


if __name__ == "__main__":
    run(update)
