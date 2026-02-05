def draw_background():
    screen.pen = brush.pattern(color.white, color.dark_grey, 23)
    screen.clear()


def draw_header():
    # create animated header text
    label = "BadgeOS v4.03"
    w, _ = screen.measure_text(label)
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
    screen.text(label, *pos)

    # draw the battery indicator
    if badge.is_charging():
        battery_level = (badge.ticks / 20) % 100
    else:
        battery_level = badge.battery_level()
    pos = (screen.width - 30, 4)
    size = (16, 8)
    screen.pen = color.white
    screen.shape(shape.rectangle(pos[0] - 3, 0, size[0] + 7, 15))
    screen.pen = color.black
    screen.shape(shape.rectangle(*pos, *size))
    screen.shape(shape.rectangle(pos[0] + size[0], pos[1] + 2, 1, 4))
    screen.pen = color.white
    screen.shape(shape.rectangle(pos[0] + 1, pos[1] + 1, size[0] - 2, size[1] - 2))

    # draw the battery fill level
    width = ((size[0] - 4) / 100) * battery_level
    screen.pen = color.black
    screen.shape(shape.rectangle(pos[0] + 2, pos[1] + 2, width, size[1] - 4))
