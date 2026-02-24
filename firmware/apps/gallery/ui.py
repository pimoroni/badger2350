

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


def draw_window(r):

    screen.pen = color.black
    screen.shape(shape.rectangle(r.x + 2, r.y + 2, r.w, r.h))
    screen.pen = color.white
    screen.shape(shape.rectangle(r.x, r.y, r.w, r.h))
    screen.pen = color.black
    screen.shape(shape.rectangle(r.x, r.y, r.w, r.h).stroke(1))


def draw_alert(text):
    badge.mode(FAST_UPDATE)

    draw_header("Gallery", rect(-1, -1, screen.width, 16))
    r = rect(10, 40, screen.width - 20, 100)
    draw_window(r)

    draw_header("Alert", r)

    tw, _ = screen.measure_text(text)
    tx = r.x + (r.w // 2) - (tw // 2)

    screen.text(text, tx, r.y + 45)

    display.update()
