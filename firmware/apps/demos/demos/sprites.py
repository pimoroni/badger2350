import math
import random

DITHER = True

skull = image.load("/system/assets/skull.png")


def update(step):
  random.seed(0)

  phase = step / 4

  for i in range(30):
    s = (math.sin(phase) * 1) + 2

    skull.alpha = int((math.sin(phase + i * 0.3) + 1) * 127)

    x = math.sin(i + phase / 2) * 40
    y = math.cos(i + phase / 2) * 40

    pos = vec2(x + rnd(-20, screen.width), y + rnd(-20, screen.height))

    dr = rect(
      pos.x, pos.y, 32 * s, 24 * s
    )
    screen.blit(skull, dr)
