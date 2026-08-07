import math
import random

DITHER = True


def update(step):
  random.seed(0)

  phase = step / 4

  for i in range(50):
    x = math.sin(i + phase) * 40
    y = math.cos(i + phase) * 40

    p = vec2(x + rnd(screen.width), y + rnd(screen.height))
    p1 = vec2(p.x + rnd(-30, 30), p.y + rnd(-30, 30))
    p2 = vec2(p.x + rnd(-30, 30), p.y + rnd(-30, 30))
    p3 = vec2(p.x + rnd(-30, 30), p.y + rnd(-30, 30))

    # keep the tones below white so the palest triangles still read on the page
    screen.pen = color.rgb(rnd(200), rnd(200), rnd(200))
    screen.triangle(p1, p2, p3)
