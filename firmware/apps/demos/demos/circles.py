import math
import random

DITHER = True


def update(step):
  random.seed(0)

  phase = step / 4

  for i in range(100):
    x = math.sin(i + phase) * 40
    y = math.cos(i + phase) * 40

    p = vec2(x + rnd(screen.width), y + rnd(screen.height))
    r = rnd(5, 20)
    # keep the tones below white so the palest circles still read on the page
    screen.pen = color.rgb(rnd(200), rnd(200), rnd(200))
    screen.circle(p, r)
