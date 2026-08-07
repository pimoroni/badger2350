import math

DITHER = True


def update(step):
  screen.antialias = image.X4

  phase = step / 4

  i = math.sin(phase / 4) * 0.2 + 0.5
  f = math.sin(phase / 2) * 150
  t = f + (math.sin(phase) + 1.0) * 50 + 100

  stroke = ((math.sin(phase / 2) + 1) * 0.05) + 0.1

  shapes = [
    shape.rectangle(-1, -1, 2, 2),
    shape.rectangle(-1, -1, 2, 2).stroke(stroke),
    shape.circle(0, 0, 1),
    shape.circle(0, 0, 1).stroke(stroke),
    shape.ellipse(0, 0, 1, 0.5),
    shape.ellipse(0, 0, 1, 0.5).stroke(stroke),
    shape.star(0, 0, 5, i, 1),
    shape.star(0, 0, 5, i, 1).stroke(stroke),
    shape.squircle(0, 0, 1),
    shape.squircle(0, 0, 1).stroke(stroke),
    shape.pie(0, 0, 1, f, t),
    shape.pie(0, 0, 1, f, t).stroke(stroke),
    shape.arc(0, 0, i, 1, f, t),
    shape.arc(0, 0, i, 1, f, t).stroke(stroke),
    shape.regular_polygon(0, 0, 1, 3),
    shape.regular_polygon(0, 0, 1, 3).stroke(stroke),
    shape.line(-0.75, -0.75, 0.75, 0.75, 0.5),
    shape.line(-0.75, -0.75, 0.75, 0.75, 0.5).stroke(stroke),
  ]

  for y in range(4):
    for x in range(4):
      i = y * 4 + x

      scale = ((math.sin(phase + i * 2) + 1) * 3) + 5

      if i < len(shapes):
        screen.pen = color.oklch(130, 128, i * 20, 255)

        shapes[i].transform = mat3().translate(x * 62 + 40, y * 40 + 24).rotate(step * 3).scale(scale)
        screen.shape(shapes[i])
