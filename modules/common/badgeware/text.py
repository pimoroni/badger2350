import builtins


def pen_glyph_renderer(image, parameters, measure):
    if measure:
        return 0
    image.pen = color.rgb(*(int(c) for c in parameters))
    return None


# Sprites registered by name for the inline [sprite:name] renderer.
SPRITES = {}


def add_sprite(name, img):
    SPRITES[name] = img


def sprite_glyph_renderer(image, parameters, measure):
    img = SPRITES[parameters[0]]
    if measure:
        return img.width
    image.blit(img, image.cursor)
    return None


# Built-in inline glyph renderers, keyed by the [code] used in text(). A renderer
# is fn(image, params, measure): return the advance width when measure is True,
# else draw (reading image.cursor for position) and return None. Extend with
# add_glyph(name, fn); add_glyph(name, None) removes one. The native text()
# layout resolves markup against this dict (handed over below).
GLYPH_RENDERERS = {"pen": pen_glyph_renderer, "sprite": sprite_glyph_renderer}


class _text:
    # Draw scrolling text into a given window.
    @staticmethod
    def scroll(text, font_face=None, font_size=None, target=None, speed=25, gap=None, align="middle"):
        font_face = font_face or font.sins

        is_vector_font = isinstance(font_face, vector_font)

        if is_vector_font and font_size is None:
            raise ValueError("scroll_text: vector fonts require a font_size")

        # Bitmap fonts take an integer scale (1, 2, 3, ...); default to 1x so we
        # pass a real scale through rather than None (the text API rejects None).
        if not is_vector_font and font_size is None:
            font_size = 1

        target = target or screen
        target.font = font_face

        tw, th = target.measure_text(text, font_size)

        if is_vector_font:
            th = font_size

        scroll_distance = tw + (gap if isinstance(gap, int) else target.width)

        t_start = badge.ticks

        offset_y = align if isinstance(align, int) else 0

        if align == "middle":
            offset_y = (target.height - th) // 2

        if align == "bottom":
            offset_y = target.height - th

        offset = vec2(0, offset_y)

        def update():
            timedelta = badge.ticks - t_start
            timedelta /= 1000 / speed
            progress = timedelta / scroll_distance
            timedelta %= scroll_distance
            timedelta /= scroll_distance

            if isinstance(gap, int):
                offset.x = -scroll_distance * timedelta
            else:
                offset.x = target.width - (scroll_distance * timedelta)

            target.font = font_face

            # font_size is the point size for vector fonts and the integer scale
            # for bitmap fonts (see picovector image.text).
            target.text(text, offset, font_size)

            if isinstance(gap, int):
                while offset.x + tw < target.width:
                    offset.x += tw + gap
                    target.text(text, offset, font_size)

            return progress

        return update


# Hand the native screen.text() markup layout our renderer registry. It reads
# this same dict, so the built-in pen/sprite (and anything registered later via
# add_glyph) are visible without a native GC root pointer.
image._set_glyph_registry(GLYPH_RENDERERS)  # noqa: SLF001

builtins.text = _text
builtins.add_glyph = image.add_glyph
builtins.add_sprite = add_sprite
