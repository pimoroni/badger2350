import math
import random

DITHER = True


def update(step):
  random.seed(0)

  phase = step / 8

  for i in range(100):
    x = math.sin(i + phase) * 40
    y = math.cos(i + phase) * 40
    # endpoints overrun the screen so the lines run off all four edges
    p1 = vec2(x + rnd(-50, screen.width + 50), y + rnd(-50, screen.height + 50))
    p2 = vec2(x + rnd(-50, screen.width + 50), y + rnd(-50, screen.height + 50))
    # single pixel lines need dark tones to survive the dither
    screen.pen = color.rgb(rnd(140), rnd(140), rnd(140))
    screen.line(p1, p2)
