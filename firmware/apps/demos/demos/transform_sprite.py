import math

DITHER = True

skull = image.load("/system/assets/skull.png")


def magic_sprite(src, pos, scale=1, angle=0):
  w, h = src.width, src.height
  t = mat3().translate(*pos).scale(scale, scale).rotate(angle).translate(-w / 2, -h)
  screen.pen = brush.image(src)
  rect = shape.rectangle(0, 0, w, h)
  rect.transform = t
  screen.shape(rect)


def update(step):
  phase = step / 4
  scale = (math.sin(phase) + 1.0) * 2 + 1
  angle = math.cos(phase / 2) * 100
  magic_sprite(skull, (screen.width / 2, screen.height / 2 + 30), scale, angle)
