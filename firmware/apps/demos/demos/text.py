import math

# The pixel font draws without antialiasing, so the frame needs no dither pass;
# the [pen:...] tags pick greys the panel can show directly. The sprite is
# dithered once at load so it survives being blitted into the text run.
skull = image.load("/system/assets/skull.png")
skull.dither()
add_sprite("skull", skull)


# [pen:r,g,b] and [sprite:skull] use the built-in renderers; register a custom
# [circle] renderer with add_glyph. A renderer is fn(image, params, measure): it
# returns its advance width when measuring, else draws at image.cursor.
def circle_glyph_renderer(image, _parameters, measure):
  if measure:
    return 12

  image.shape(shape.circle(image.cursor.x + 6, image.cursor.y + 7, 6))
  return None


add_glyph("circle", circle_glyph_renderer)


def update(step):
  screen.font = font.compass

  message = """[pen:64,64,64]Upon the mast I gleam and grin, A sentinel of bone and sin. Wind and thunder, night and hull- None fear the sea like a [pen:0,0,0]pirate skull[pen:64,64,64][sprite:skull].
"""

  x = 5
  y = 5
  width = math.sin(step / 4) * 60 + 170
  height = screen.height - y - 18  # fit the box on-screen, leaving room for the caption
  bounds = rect(x, y, width, height)

  screen.pen = color.black
  screen.text(message, bounds, line_height=1, word_spacing=1.05)

  screen.pen = color.rgb(160, 160, 160)
  screen.line(bounds.x, bounds.y, bounds.x + bounds.w, bounds.y)
  screen.line(bounds.x, bounds.y, bounds.x, bounds.y + bounds.h)
  screen.line(bounds.x, bounds.y + bounds.h, bounds.x + bounds.w, bounds.y + bounds.h)
  screen.line(bounds.x + bounds.w, bounds.y, bounds.x + bounds.w, bounds.y + bounds.h)
