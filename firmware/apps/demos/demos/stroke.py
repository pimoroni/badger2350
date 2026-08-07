import math

DITHER = True


def update(step):
  screen.antialias = image.X4

  # Step the stroke thickness so the alignment modes are easy to compare.
  thickness = (math.sin(step / 3) + 1) * 5 + 1

  spacing = screen.width / 4

  aligns = [
    ("inner", shape.ALIGN_INNER),
    ("centre", shape.ALIGN_CENTER),
    ("outer", shape.ALIGN_OUTER),
  ]

  # top row strokes each star as a closed loop, bottom row as an open polyline
  # (the open stars don't join the last edge back to the first).
  rows = [
    ("closed", screen.height * 0.30, True),
    ("open", screen.height * 0.68, False),
  ]

  for row_label, cy, closed in rows:
    for i, (label, align) in enumerate(aligns):
      cx = spacing * (i + 1)

      screen.pen = color.oklch(130, 128, i * 60, 255)
      flags = align | (0 if closed else shape.PATH_OPEN)
      screen.shape(shape.star(cx, cy, 5, 11, 24).stroke(thickness, flags))

      screen.pen = color.black
      screen.text(label, cx - 18, cy + 38)

    screen.pen = color.black
    screen.text(row_label, 2, cy)
