import builtins
import os


def pen_glyph_renderer(image, parameters, _cursor, measure):
    if measure:
        return 0
    image.pen = color.rgb(*(int(c) for c in parameters))
    return None

class _text:
    @staticmethod
    def tokenise(image, text, glyph_renderers=None, size=24):
        WORD = 1
        SPACE = 2
        LINE_BREAK = 3

        default_glyph_renderers = {"pen": pen_glyph_renderer}
        default_glyph_renderers.update(glyph_renderers or {})

        tokens = []

        for line in text.splitlines():
            start, end = 0, 0
            i = 0
            while end < len(line):
                # check for a glyph_renderer
                if default_glyph_renderers and line.find("[", start) == start:
                    glyph_end = line.find("]", start)
                    # look ahead to see if this is an escape code
                    glyph_renderer = line[start + 1:glyph_end]
                    parameters = []
                    if ":" in glyph_renderer:
                        code, parameters = glyph_renderer.split(":")
                        parameters = parameters.split(",")
                    else:
                        code = glyph_renderer

                    if code in default_glyph_renderers:
                        w = default_glyph_renderers[code](None, parameters, None, True)
                        tokens.append((default_glyph_renderers[code], w, tuple(parameters)))
                        start = glyph_end + 1
                        continue

                i += 1

                # search for the next space or glyph
                next_space = line.find(" ", start)
                next_glyph = line.find("[", start + 1)

                end = min(next_space, next_glyph)
                if end == -1:
                    end = max(next_space, next_glyph)
                if end == -1:
                    end = len(line)

                # measure the text up to the space
                if end > start:
                    if isinstance(image.font, font):
                        width, _ = image.measure_text(line[start:end], size)
                    else:
                        width, _ = image.measure_text(line[start:end])
                    tokens.append((WORD, width, line[start:end]))

                start = end
                if end < len(line) and line[end] == " ":
                    tokens.append((SPACE,))
                    start += 1

            tokens.append((LINE_BREAK,))

        return tokens

    @staticmethod
    def draw(image, text, bounds=None, line_spacing=1, word_spacing=1, size=24):
        WORD = 1
        SPACE = 2
        LINE_BREAK = 3

        if bounds is None:
            bounds = rect(0, 0, image.width, image.height)
        else:
            bounds = rect(int(bounds.x), int(bounds.y), int(bounds.w), int(bounds.h))

        if isinstance(text, str):
            tokens = _text.tokenise(image, text, size=size)
        else:
            tokens = text

        old_clip = image.clip
        image.clip = bounds

        c = vec2(bounds.x, bounds.y)
        b = rect()
        for token in tokens:
            font_height = size if isinstance(image.font, font) else image.font.height
            if token[0] == WORD:
                if c.x + token[1] > bounds.x + bounds.w:
                    c.x = bounds.x
                    c.y += font_height * line_spacing
                if isinstance(image.font, font):
                    image.text(token[2], c.x, c.y, size)
                else:
                    image.text(token[2], c.x, c.y)
                c.x += token[1]
            elif token[0] == SPACE:
                c.x += (font_height / 3) * word_spacing
            elif token[0] == LINE_BREAK:
                c.x = bounds.x
                c.y += font_height * line_spacing
            else:
                if c.x + token[1] > bounds.x + bounds.w:
                    c.x = bounds.x
                    c.y += font_height * line_spacing

                token[0](image, token[2], c, False)
                c.x += token[1]

            b.w = max(b.w, c.x)
            b.h = max(b.h, c.y)

        image.clip = old_clip
        return b

    # Draw scrolling text into a given window
    @staticmethod
    def scroll(text, font_face=None, bg=None, fg=None, target=None, speed=25, continuous=False, font_size=None):
        font_face = font_face or rom_font.sins
        fg = fg or color.rgb(128, 128, 128)

        is_vector_font = isinstance(font_face, font)

        if is_vector_font and font_size is None:
            raise ValueError("scroll_text: vector fonts require a font_size")

        target = target or screen.window(0, 0, screen.width, screen.height)
        target.font = font_face

        tw, th = target.measure_text(text, font_size) if isinstance(font_face, font) else target.measure_text(text)

        if is_vector_font:
            th = font_size

        scroll_distance = tw + (0 if continuous else target.width)

        t_start = badge.ticks

        offset = vec2(0, (target.height - th) // 2)

        def update():
            timedelta = badge.ticks - t_start
            timedelta /= 1000 / speed
            progress = timedelta / scroll_distance
            timedelta %= scroll_distance
            timedelta /= scroll_distance

            if continuous:
                offset.x = -scroll_distance * timedelta
            else:
                offset.x = target.width - (scroll_distance * timedelta)

            target.font = font_face
            if bg is not None:
                target.pen = bg
                target.clear()
            target.pen = fg

            # The "font_size" argument is ignored for vector text
            target.text(text, offset, font_size)

            if continuous:
                target.text(text, offset + vec2(tw, 0), font_size)

            return progress

        return update


def load_font(font_file):
    search_paths = ("/rom/fonts", "/system/assets/fonts", "/fonts", "/assets", "")
    file = font_file

    try:
        return getattr(rom_font, font_file)
    except AttributeError:
        pass

    # Remove /rom/fonts if searching for .af files
    if file.endswith(".af"):
        search_paths = search_paths[1:]

    extensions = (".af", ".ppf") if not file.endswith(".af") and not file.endswith(".ppf") else ("", )

    for search_path in search_paths:
        for ext in extensions:
            path = search_path + f"/{file}{ext}"
            if file_exists(path) and not is_dir(path):
                return font.load(path) if path.endswith(".af") else pixel_font.load(path)

    raise OSError(f'Font "{font_file}" not found!')


class ROMFonts:
    def __getattr__(self, key):
        try:
            return pixel_font.load(f"/rom/fonts/{key}.ppf")
        except OSError as e:
            raise AttributeError(f"Font {key} not found!") from e

    def __dir__(self):
        return [f[:-4] for f in os.listdir("/rom/fonts") if f.endswith(".ppf")]


builtins.rom_font = ROMFonts()
builtins.load_font = load_font
builtins.text = _text
