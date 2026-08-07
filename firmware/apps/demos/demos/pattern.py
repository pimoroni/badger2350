import math

# Pattern brushes are already 1-bit stipple, so they need no dither pass; the
# foreground just has to be one of the panel's grey levels.


def update(step):
  cx = screen.width / 2
  cy = screen.height / 2
  phase = step / 4

  custom_pattern = brush.pattern(color.black, color.transparent, (
    0b00000000,
    0b01111110,
    0b01000010,
    0b01011010,
    0b01011010,
    0b01000010,
    0b01111110,
    0b00000000))
  screen.pen = custom_pattern
  screen.shape(shape.circle(cx + math.cos(phase) * 30, cy + math.sin(phase / 2) * 30, 34))

  built_in_pattern = brush.pattern(color.dark_grey, color.transparent, 11)
  screen.pen = built_in_pattern
  screen.shape(shape.circle(cx + math.sin(phase * 2) * 60, cy + math.cos(phase) * 60, 34))

  built_in_pattern = brush.pattern(color.rgb(160, 160, 160), color.transparent, 8)
  screen.pen = built_in_pattern
  screen.shape(shape.circle(cx + math.cos(phase * 2) * 60, cy + math.sin(phase) * 60, 34))
