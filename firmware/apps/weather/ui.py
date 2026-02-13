import math


def draw_header(t, r):
    tw, _ = screen.measure_text(t)
    pos = (r.x + (r.w / 2) - (tw / 2), r.y + 1)

    screen.pen = color.white
    screen.shape(shape.rectangle(r.x + 1, r.y + 1, r.w - 2, 15))

    lx = r.x + 4
    lw = r.x + (r.w - 6)
    screen.pen = color.black

    screen.line(lx, r.y + 4, lw, r.y + 4)
    screen.line(lx, r.y + 6, lw, r.y + 6)
    screen.line(lx, r.y + 8, lw, r.y + 8)
    screen.line(lx, r.y + 10, lw, r.y + 10)
    screen.line(r.x, r.y + 15, r.x + r.w, r.y + 15)

    screen.pen = color.white
    screen.shape(shape.rectangle(pos[0] - 5, pos[1], tw + 10, 14))

    screen.pen = color.black
    screen.text(t, *pos)


def angle_to_vec2(angle, radius):
    angle = math.radians(angle - 90)
    return vec2(math.cos(angle) * radius, math.sin(angle) * radius)


def custom_arrow(sweep=120):
    sweep += 90
    return shape.custom([
        angle_to_vec2(0, radius=1),
        angle_to_vec2(-sweep, radius=0.5),
        vec2(0, 0),
        angle_to_vec2(sweep, radius=0.5)
    ])


def thermometer(unit_length=6, thickness=1.0, fill=1.0):
    unit_length *= fill
    unit_length += (1.0 - thickness) / 2
    resolution = 24
    bulb_angle = 290
    points = []
    start = None
    for i in range(resolution + 1):
        a = bulb_angle / resolution * i + ((360 - bulb_angle) / 2)
        v = angle_to_vec2(a, thickness)
        start = start or v
        points.append(v)
    end = v

    # fudge the part where the stem connects to the bulb
    # to try and get the stem walls as thick as the bulb
    start.x -= (1.0 - thickness) / 2
    end.x += (1.0 - thickness) / 2
    start.y -= (1.0 - thickness) / 2
    end.y -= (1.0 - thickness) / 2

    # Find half the distance between end and start (end radius)
    r = (end - start).x / 2

    # Find the point exactly between the end and start
    o = start + (end - start) / 2 + vec2(0, -unit_length)
    points.append(end + vec2(0, -unit_length))

    # Draw the end roundover
    for i in range(resolution):
        v = angle_to_vec2(i * (180 / resolution) + 90, r) + o
        points.append(v)
    points.append(start + vec2(0, -unit_length))
    return shape.custom(points)


def draw_window(r):

    screen.pen = color.black
    screen.shape(shape.rectangle(r.x + 2, r.y + 2, r.w, r.h))
    screen.pen = color.white
    screen.shape(shape.rectangle(r.x, r.y, r.w, r.h))
    screen.pen = color.black
    screen.shape(shape.rectangle(r.x, r.y, r.w, r.h).stroke(1))


def draw_alert(text):
    badge.mode(FAST_UPDATE)

    draw_header("Weather", rect(-1, -1, screen.width, 16))
    r = rect(10, 40, screen.width - 20, 100)
    draw_window(r)

    draw_header("Alert", r)

    tw, _ = screen.measure_text(text)
    tx = r.x + (r.w // 2) - (tw // 2)

    screen.text(text, tx, r.y + 45)

    display.update()
