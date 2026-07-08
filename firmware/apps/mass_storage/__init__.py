import time
import powman

# Enter USB Mass Storage mode from a *clean* boot rather than running it inline on
# top of the live badge framework (wifi/bt/display all still holding resources).
#
# powman.reset_into_msc() sets powman's persistent "double-tap" flag and reboots.
# On the next boot the badge reports a WAKE_DOUBLETAP wake reason, so main.py
# takes the exact same path as a physical double-tap and imports _msc.


def show_message():
    screen.pen = color.black
    screen.shape(shape.rectangle(0, 0, screen.width, screen.height))
    try:
        screen.font = rom_font.absolute
    except OSError:
        pass
    screen.pen = color.white
    lines = ("Switching to", "USB Disk Mode...")
    _, line_height = screen.measure_text(lines[0])
    y = (screen.height - line_height * len(lines)) / 2
    for line in lines:
        width, _ = screen.measure_text(line)
        screen.text(line, (screen.width - width) / 2, y)
        y += line_height
    display.update()


show_message()
time.sleep(0.4)  # let the message land before we drop off the bus

powman.reset_into_msc()
