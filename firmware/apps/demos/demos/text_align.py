# Demonstrates text.draw() alignment (align / valign) and ellipsis clipping.
# The top box cycles through every align x valign combination; the bottom box
# feeds in far too much text with ellipsis=True so the overflow is trimmed to a
# trailing "..." instead of spilling past the edge.

message = "Align the quick brown fox and watch it move."

overflow = (
    "This paragraph is deliberately far too long to fit inside its little box. "
    "Rather than spilling past the edge, text.draw trims what doesn't fit and "
    "finishes the last visible line with an ellipsis so it stays tidy."
)

ALIGNS = ("left", "center", "right")
VALIGNS = ("top", "middle", "bottom")


def framed(b):
    screen.pen = color.rgb(70, 90, 110)
    screen.rectangle(b.x - 1, b.y - 1, b.w + 2, b.h + 2)
    screen.pen = color.rgb(18, 22, 30)
    screen.rectangle(b.x, b.y, b.w, b.h)


def update():
    screen.font = font.sins

    w, h = screen.width, screen.height
    pad = 4

    # advance through the 9 combos about once a second
    step = round(badge.ticks / 900)
    align = ALIGNS[step % 3]
    valign = VALIGNS[(step // 3) % 3]

    align_box = rect(pad, pad + 12, w - pad * 2, h // 2 - pad - 12)
    clip_box = rect(pad, h // 2 + pad + 12, w - pad * 2, h // 2 - pad * 2 - 12)

    screen.pen = color.rgb(150, 170, 190)
    screen.text("align={} valign={}".format(align, valign), pad, pad)

    framed(align_box)
    screen.pen = color.rgb(235, 230, 215)
    text.draw(screen, message, align_box, align=align, valign=valign)

    screen.pen = color.rgb(150, 170, 190)
    screen.text("ellipsis=True", pad, h // 2 + pad)

    framed(clip_box)
    screen.pen = color.rgb(235, 210, 160)
    text.draw(screen, overflow, clip_box, ellipsis=True)
