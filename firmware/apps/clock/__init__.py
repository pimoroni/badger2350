import sys
import os

sys.path.insert(0, "/system/apps/clock")
sys.path.insert(0, "/")
os.chdir("/system/apps/clock")

from badgeware import State
import time
import ntptime
from daylightsaving import DaylightSavingPolicy, DaylightSaving
from usermessage import user_message, center_text, stretch_text
from machine import RTC
import math
import secrets
import wifi


# Set the LED to light whenever the unit's active.
badge.set_caselights(0.1)

# Clear any previously set RTC flags.
rtc.clear_alarm()


# Making classes for which clock is displayed, so we can refer to them by name.
class DisplayType:
    textclock = 1
    dotsclock = 2
    scribble = 3
    sevenseg = 4


secrets.require("REGION", "TIMEZONE")

REGION = secrets.REGION
TIMEZONE = secrets.TIMEZONE

# Setting up default values for the first run, and loading in the state with the
# user choices if the file's there.
state = {
    "dark_mode": True,
    "clock_style": 4,
    "first_run": True
}

State.load("clock", state)

if state["first_run"]:
    icons = SpriteSheet("assets/icons.png", 5, 1)

# Loading all the assets.
textclock_font = rom_font.ziplock
dots_font = rom_font.futile
scribble_font = rom_font.ziplock

palette = (color.rgb(44, 44, 44), color.rgb(44, 44, 44, 100), color.white, color.rgb(255, 255, 255, 100))

if state["dark_mode"]:
    faded_brush = palette[3]
    bg_brush = palette[0]
    drawing_brush = palette[2]
else:
    faded_brush = palette[1]
    bg_brush = palette[2]
    drawing_brush = palette[0]

if state["clock_style"] == DisplayType.scribble:
    numerals = SpriteSheet("assets/scribble_num.png", 10, 1)
    background = image.load("assets/scribble_bg.png")
    clock_dots = image.load("assets/scribble_dots.png")
elif state["clock_style"] == DisplayType.sevenseg:
    numerals = SpriteSheet("assets/digital_num.png", 10, 1)
    background = None
    clock_dots = image.load("assets/digital_dots.png")

month_days = {
    1: 31,
    2: 28,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31
}

calendar_months = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December"
}

# These are the different Daylight Saving time zones, according to the Wikipedia article.
# Timezones are incredibly complex, we've covered the main ones here.
# "zonename": (hemisphere, week, month, weekday, hour, timezone, minutes clocks change by)
# Israel and Palestine each follow different daylight saving rules from standard, and are not included here.
regions = {
    "us": (0, 2, 3, 6, 2, 1, 11, 6, 2, 60),
    "cuba": (0, 2, 3, 6, 0, 1, 11, 6, 1, 60),
    "eu": (0, 0, 3, 6, 1, 0, 10, 6, 1, 60),
    "moldova": (0, 0, 3, 6, 2, 0, 10, 6, 3, 60),
    "lebanon": (0, 0, 3, 6, 0, 0, 10, 6, 0, 60),
    "egypt": (0, 0, 4, 4, 0, 0, 10, 3, 24, 60),
    "chile": (1, 1, 9, 5, 24, 1, 4, 5, 24, 60),
    "australia": (1, 1, 10, 6, 2, 1, 4, 6, 3, 60),
    "nz": (1, 0, 9, 6, 2, 1, 4, 6, 3, 60)
}


def update_time(region, timezone):
    # Set the time with npt and pass it to the daylight saving calculator.
    # Pass the result to the unit's RTC.

    try:
        ntptime.settime()
        time.sleep(2)
    except OSError:
        return False

    timezone_minutes = timezone * 60

    hemisphere, week_in, month_in, weekday_in, hour_in, week_out, month_out, weekday_out, hour_out, mins_difference = regions[region]

    dstp = DaylightSavingPolicy(hemisphere, week_in, month_in, weekday_in, hour_in, timezone_minutes + mins_difference)
    stdp = DaylightSavingPolicy(hemisphere, week_out, month_out, weekday_out, hour_out, timezone_minutes)

    dst = DaylightSaving(dstp, stdp)
    t = time.mktime(time.gmtime())
    tm = time.gmtime(dst.localtime(t))
    RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
    year, month, day, dow, hour, minute, second, dow = RTC().datetime()
    rtc.datetime((year, month, day, hour, minute, second, dow))

    return True


def display_time():
    # Chooses which clock face to show based on the clock_style global.

    global clock_dots, numerals, background

    currenttime = rtc.datetime()

    if state["clock_style"] == DisplayType.textclock:
        draw_text_clock(currenttime)

    elif state["clock_style"] == DisplayType.dotsclock:
        draw_dots_clock(currenttime)

    # For the scribble and seven segment displays, we're reusing the same variables
    # for numerals, dots etc and just loading different files into them to save memory.
    elif state["clock_style"] == DisplayType.scribble:
        numerals = SpriteSheet("assets/scribble_num.png", 10, 1)
        background = image.load("assets/scribble_bg.png")
        clock_dots = image.load("assets/scribble_dots.png")
        screen.font = scribble_font
        draw_scribble_clock(currenttime)

    elif state["clock_style"] == DisplayType.sevenseg:
        numerals = SpriteSheet("assets/digital_num.png", 10, 1)
        clock_dots = image.load("assets/digital_dots.png")
        background = None
        draw_sevenseg_clock(currenttime)


def draw_sevenseg_clock(currenttime):
    # For Badger's seven segment clock, the numerals are PNGs.

    screen.antialias = image.X4

    # This is how far out from the centre each set of digits gets moved to make room for the dots.
    digit_offset = 6

    # This doesn't use light mode, so we disable it here.
    this_drawing_brush = bg_brush
    this_bg_brush = color.black
    if state["dark_mode"]:
        this_drawing_brush = drawing_brush
        this_bg_brush = color.black

    # Start with a blank slate.
    screen.pen = this_bg_brush
    screen.clear()

    digit_h = numerals.sprite(0, 0).height
    digit_y = math.floor((screen.height - digit_h) / 2)

    screen.pen = this_drawing_brush

    # The whole next section draws bars of increasing thickness diagonally
    # across the screen, as well as the filled in sections to the sides.
    bar_width = 100

    y = 0
    leftx = (screen.width - screen.height - bar_width) / 2
    rightx = leftx + bar_width
    offset = 0

    seconds_spacing = 6  # Distance between the filled sections and the stripes.

    # Draws the upper right filled section.
    seconds_x_start = rightx + seconds_spacing
    seconds_y_start = 0
    seconds_xy_offset = digit_y - 8
    screen.shape(shape.custom([
        vec2(seconds_x_start, seconds_y_start),
        vec2(screen.width, seconds_y_start),
        vec2(screen.width, seconds_xy_offset),
        vec2(seconds_x_start + seconds_xy_offset - seconds_y_start, seconds_xy_offset)
    ]))

    # Draws the stripes increasing in thiccness until it gets to half way down the screen.
    while y <= screen.height / 2:
        seg_path = [vec2(leftx, y),
                    vec2(rightx, y),
                    vec2(rightx + offset, y + offset),
                    vec2(leftx + offset, y + offset)]
        seg = shape.custom(seg_path)
        screen.shape(seg)
        offset += 1
        y += 2 * offset
        leftx += 2 * offset
        rightx += 2 * offset

    y = screen.height
    rightx = screen.width - ((screen.width - screen.height - bar_width) / 2)
    leftx = rightx - bar_width

    # Then the lower left filled area...
    seconds_x_start = leftx - seconds_spacing
    screen.shape(shape.custom([
        vec2(seconds_x_start, screen.height - seconds_y_start),
        vec2(0, screen.height - seconds_y_start),
        vec2(0, screen.height - seconds_xy_offset),
        vec2(seconds_x_start - seconds_xy_offset + seconds_y_start, screen.height - seconds_xy_offset)]))

    # Just like above, draws stripes increasing in thiccness from the bottom of the screen.
    offset = 0
    while y >= 60:
        seg_path = [vec2(leftx, y), vec2(rightx, y), vec2(rightx - offset, y - offset), vec2(leftx - offset, y - offset)]
        seg = shape.custom(seg_path)
        screen.shape(seg)
        offset += 1
        y -= 2 * offset
        leftx -= 2 * offset
        rightx -= 2 * offset

    # Blank out the central section so we've a clean space to draw the digits.
    screen.pen = this_bg_brush
    screen.shape(shape.rectangle(0, digit_y - seconds_spacing, screen.width, digit_h + (2 * seconds_spacing)))

    # Draw the dots in between the numerals.
    screen.blit(clock_dots, vec2((screen.width / 2) - (clock_dots.width / 2), digit_y))

    # Then finally draw the digit sprites.
    hour = currenttime[3]
    minute = currenttime[4]

    draw_digits(hour, minute, numerals, digit_offset, digit_y)


def draw_scribble_clock(currenttime):
    # Scribble is simpler than 7 segment as there's no vector drawing to figure out,
    # all the hard work is done by the images.

    # It doesn't do dark mode, so here we're setting a new drawing brush
    # based on whichever regular brush is the bright one.
    this_drawing_brush = drawing_brush
    if state["dark_mode"]:
        this_drawing_brush = bg_brush

    # First draw the background
    screen.blit(background, vec2(0, 0))

    # Then make up a string for the date and draw it.
    year = currenttime[0]
    month = calendar_months[currenttime[1]]
    mday = currenttime[2]

    suffix = "th"
    mday_units = mday % 10
    if mday_units == 1:
        suffix = "st"
    if mday_units == 2:
        suffix = "nd"
    if mday_units == 3:
        suffix = "rd"

    date = str(mday) + suffix + " " + month + " " + str(year)

    screen.pen = this_drawing_brush
    center_text(date, 155)

    # Draw the digits just like in the 7 segment clock...
    hour = currenttime[3]
    minute = currenttime[4]

    digit_h = numerals.sprite(0, 0).height
    digit_y = math.floor((screen.height - digit_h) / 2)

    draw_digits(hour, minute, numerals, 0, digit_y)
    screen.blit(clock_dots, vec2((screen.width / 2) - (clock_dots.width / 2), digit_y + 10))


def draw_digits(hour, minute, spritesheet, center_offset, y_pos):

    # This is used for both the nixie and digital clocks.

    # Simply divide the hours and minutes into individual digits...
    hourtens = math.floor(hour / 10)
    hourunits = hour % 10
    minutetens = math.floor(minute / 10)
    minuteunits = minute % 10

    # ...and then use that to pick a sprite from the spritesheet of numerals.
    screen.blit(spritesheet.sprite(hourtens, 0), vec2(0 - center_offset, y_pos))
    screen.blit(spritesheet.sprite(hourunits, 0), vec2(66 - center_offset, y_pos))
    screen.blit(spritesheet.sprite(minutetens, 0), vec2(132 + center_offset, y_pos))
    screen.blit(spritesheet.sprite(minuteunits, 0), vec2(198 + center_offset, y_pos))


# This method draws a row of circles across a given width, sizing them so they fill the
# width with a specified gap, and optional double space every X dots.
def draw_dot_row(y, width, total, filled, space_size, space_every):
    # First work out how many spaces.
    num_spaces = total - 1
    if space_every > 0:
        num_spaces += total / space_every
    total_space_width = num_spaces * space_size

    # That gives us how much space we have to work with for the dots.
    # We work out their radius, then get an actual width based on that rounded radius.
    total_dot_width = width - total_space_width
    dot_radius = (total_dot_width / total) / 2
    actual_dots_width = dot_radius * 2 * total

    # Then we can figure out where to draw the first dot.
    total_width = actual_dots_width + total_space_width
    dot_x = dot_radius

    w = int(total_width)
    h = int(dot_radius * 2)

    dot_row = image(w, h)
    dot_row.antialias = image.X4
    dot_row.pen = drawing_brush

    # Now we just iterate through, drawing a dot and increasing the x co-ordinate each time.
    for i in range(total):
        if filled > i:
            dot_row.pen = drawing_brush
        else:
            dot_row.pen = faded_brush
        dot_row.shape(shape.circle(dot_x, dot_radius, dot_radius))
        dot_x += (2 * dot_radius) + space_size
        if space_every > 0 and (i + 1) % space_every == 0:
            dot_x += space_size

    x_pos = ((screen.width - total_width) / 2)
    screen.blit(dot_row, vec2(x_pos, y))

    # We return the height of the row so we can add it to y for the next row.
    return dot_radius * 2


def draw_dots_clock(currenttime):
    # Drawing the dots clock just involves writing the text captions and
    # creating the rows of dots using the above method.

    screen.antialias = image.X4
    screen.font = dots_font

    screen.pen = bg_brush
    screen.clear()

    row_spacing = 1
    border = 7

    month = currenttime[1]
    mday = currenttime[2]
    hours = currenttime[3]
    minutes = currenttime[4]

    # The draw_dot_row and stretch_text functions both return the height of what they've
    # just rendered, so we just add that plus a small gap to the y coordinate each time
    # to move down the screen as we draw.
    y = 0

    y += stretch_text("MONTH", border, y, screen.width - (2 * border), drawing_brush)

    y += draw_dot_row(y, screen.width - (2 * border), 12, month, 2, 0) + (2 * row_spacing) + 5

    y += stretch_text("DAY", border, y, screen.width - (2 * border), drawing_brush)

    y += draw_dot_row(y, screen.width - (2 * border), month_days[month], mday, 2, 0) + (2 * row_spacing) + 5

    y += stretch_text("HOUR", border, y, screen.width - (2 * border), drawing_brush)

    y += draw_dot_row(y, screen.width - (2 * border), 24, hours, 2, 4) + (2 * row_spacing) + 5

    y += stretch_text("MINUTE", border, y, screen.width - (2 * border), drawing_brush)

    # Minutes get two rows, so there's a little maths to do to split the total
    # between the two rows.
    y += draw_dot_row(y, screen.width - (2 * border), 30, minutes, 2, 5) + (2 * row_spacing)
    if currenttime[4] > 30:
        minutes -= 30
    else:
        minutes = 0
    y += draw_dot_row(y, screen.width - (2 * border), 30, minutes, 2, 5) + (2 * row_spacing) + 5


def draw_text_clock(currenttime):
    # The text clock involves solely drawing text.

    screen.pen = bg_brush
    screen.clear()

    screen.font = textclock_font

    # First of all we're making a list of lists containing all of the words that are
    # going on the screen.
    words = [["it", "is", "about", "half", "twenty"],
             ["quarter", "ten\n", "five\n", "past", "to"],
             ["one", "two", "three", "four", "five"],
             ["six", "seven", "eight", "nine", "ten"],
             ["eleven", "twelve", "o'clock", "on"],
             ["sunday", "monday", "tuesday"],
             ["wednesday", "thursday"],
             ["friday", "saturday", "morning"],
             ["afternoon", "evening", "night"]]

    # displayed_time contains all the words we want lit up. These ones are always lit.
    displayed_time = ["it", "is", "about", "on"]

    # We need to work out which number on a clock face we're
    # currently closest to.
    hours = currenttime[3]
    minutes_in_seconds = (currenttime[4] * 60) + currenttime[5]
    hour_portion = (minutes_in_seconds + 150) / 300
    minutes = math.floor(hour_portion)

    # Depending on that, we just do a bunch of checks to decide which words
    # to put into which variables.
    # The newlines on the "five\n" and "ten\n" don't do anything or change
    # the way the string is displayed, but it makes it a different string
    # from the "hour" five and ten later on so they don't get mixed up.
    # If something needs to be lit we just add it to displayed_time.
    if minutes == 0 or minutes == 12:
        displayed_time.append("o'clock")
    if minutes == 1 or minutes == 11 or minutes == 5 or minutes == 7:
        displayed_time.append("five\n")
    if minutes == 2 or minutes == 10:
        displayed_time.append("ten\n")
    if minutes == 3 or minutes == 9:
        displayed_time.append("quarter")
    if minutes == 4 or minutes == 8 or minutes == 5 or minutes == 7:
        displayed_time.append("twenty")
    if minutes == 6:
        displayed_time.append("half")

    if minutes <= 6 and minutes > 0:
        displayed_time.append("past")
    elif minutes == 12:
        hours += 1
    elif minutes > 6 and minutes < 12:
        displayed_time.append("to")
        hours += 1
    if hours > 23:
        hours -= 24

    if hours == 0 or hours == 12:
        displayed_time.append("twelve")
    if hours == 1 or hours == 13:
        displayed_time.append("one")
    if hours == 2 or hours == 14:
        displayed_time.append("two")
    if hours == 3 or hours == 15:
        displayed_time.append("three")
    if hours == 4 or hours == 16:
        displayed_time.append("four")
    if hours == 5 or hours == 17:
        displayed_time.append("five")
    if hours == 6 or hours == 18:
        displayed_time.append("six")
    if hours == 7 or hours == 19:
        displayed_time.append("seven")
    if hours == 8 or hours == 20:
        displayed_time.append("eight")
    if hours == 9 or hours == 21:
        displayed_time.append("nine")
    if hours == 10 or hours == 22:
        displayed_time.append("ten")
    if hours == 11 or hours == 23:
        displayed_time.append("eleven")

    weekdaytime = (currenttime[0], currenttime[1], currenttime[2], currenttime[3], currenttime[4], currenttime[5], currenttime[6], 0)
    weekday = int((time.mktime(weekdaytime) // 86400) - 10957) % 7

    if weekday == 0:
        displayed_time.append("saturday")
    if weekday == 1:
        displayed_time.append("sunday")
    if weekday == 2:
        displayed_time.append("monday")
    if weekday == 3:
        displayed_time.append("tuesday")
    if weekday == 4:
        displayed_time.append("wednesday")
    if weekday == 5:
        displayed_time.append("thursday")
    if weekday == 6:
        displayed_time.append("friday")

    if hours > 4 and hours < 12:
        displayed_time.append("morning")
    elif hours >= 12 and hours < 18:
        displayed_time.append("afternoon")
    elif hours >= 18 and hours < 22:
        displayed_time.append("evening")
    else:
        displayed_time.append("night")

    # Finally we draw it all.
    border = 8
    y = border

    # Measuring some random text to get a line height.
    line_height = screen.measure_text("Anything here")
    y_spacing = (screen.height - (2 * border) - (line_height[1] * len(words))) / (len(words) - 1)

    # Then for each line we go through each word and see if it's in displayed_time. If it is we
    # draw it with the bright brush, if not we draw it with the faded brush.
    # After each word we move the x drawing position along by the word's width, plus a spacing
    # calculated by measuring all the words together, subtracting that from the screen width
    # and dividing the result by the number of words so that they're evenly spaced.
    for line in words:
        spaces = len(line) - 1
        textwidth = screen.measure_text("".join(line))
        x_spacing = (screen.width - (2 * border) - textwidth[0]) / spaces

        x = border
        for word in line:
            if word in displayed_time:
                screen.pen = drawing_brush
                displayed_time.remove(word)
            else:
                screen.pen = faded_brush
            screen.text(word, x, y)
            x += screen.measure_text(word)[0]
            x += round(x_spacing)

        y += line_height[1] + y_spacing


def intro_screen():
    # The intro screen only shows on the first run of Clock.
    # It just shows some icons to demonstrate what each button does.

    screen.pen = color.black
    screen.clear()

    screen.pen = color.white
    screen.font = textclock_font
    center_text("Welcome to Clock!", 3)

    screen.blit(icons.sprite(0, 0), vec2(35, 144))
    screen.blit(icons.sprite(1, 0), vec2(116, 144))
    screen.blit(icons.sprite(2, 0), vec2(200, 144))
    screen.blit(icons.sprite(3, 0), vec2(232, 30))

    screen.font = scribble_font
    center_text("Press any button", 40)
    center_text("to continue,", 60)
    center_text("this screen will", 80)
    center_text("not be shown again.", 100)


def switch_palette():
    # This switches between light and dark mode by making the background,
    # faded and drawing brush the appropriate light or dark values from
    # the colour palette.

    global bg_brush, drawing_brush, faded_brush

    if state["dark_mode"]:
        faded_brush = palette[3]
        bg_brush = palette[0]
        drawing_brush = palette[2]
    else:
        faded_brush = palette[1]
        bg_brush = palette[2]
        drawing_brush = palette[0]


def write_settings():
    # Simply saves the user-selected options as a state.
    State.save("clock", state)


def update():
    # Main update loop.

    global state

    # First we check if it's the first time of running, and if so show the intro screen.
    # Any face button press will move it into the regular running mode.
    if state["first_run"]:
        intro_screen()
        state["first_run"] = False
        write_settings()

    # If the year in the RTC is 2021 or earlier, we need to sync so it has the same effect as pressing B.
    # This starts the chain of connecting to the WiFi and pulling the correct time.
    elif badge.pressed(BUTTON_B) or time.gmtime()[0] <= 2021:
        user_message("Please Wait!", ["Connecting to WiFi..."])
        wifi.connect()
        # Block until WiFi is connected or an error occurs
        while not wifi.tick():
            pass
        if update_time(REGION, TIMEZONE) is False:
            user_message("Error!", ["Unable to get time", "from NTP server."])
        else:
            user_message("Update", ["Updated time", "from NTP server."])


    # And then we detect button presses and act accordingly.
    if badge.pressed(BUTTON_UP) or badge.pressed(BUTTON_DOWN):
        state["dark_mode"] = not state["dark_mode"]
        write_settings()
        switch_palette()

    elif badge.pressed(BUTTON_C):
        state["clock_style"] += 1
        if state["clock_style"] > 4:
            state["clock_style"] = 1
        write_settings()

    elif badge.pressed(BUTTON_A):
        state["clock_style"] -= 1
        if state["clock_style"] < 1:
            state["clock_style"] = 4
        write_settings()

    # We then get the current time, and set an RTC alarm to wake up at the start of
    # the next minute and run all this again, so the clock can update.
    rtc.set_alarm(minutes=1)
    display_time()


def init():
    pass


def on_exit():
    rtc.clear_alarm()


# Standalone support for Thonny debugging
if __name__ == "__main__":
    run(update, init=init, on_exit=on_exit)
