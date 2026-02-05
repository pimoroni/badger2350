import os
import math



# icon shape
shade_brush = color.rgb(0, 0, 0, 50)

cx, cy = screen.width / 2, screen.height / 2


class App:
    def __init__(self, collection, name, path, icon):
        self.active = False
        self.index = len(collection)
        self.pos = vec2((self.index % 3) * 88 + 43, (math.floor((self.index % 6) / 3)) * 78 + 55)
        self.icon = icon
        self.name = name
        self.path = path
        collection.append(self)

    def activate(self, active):
        self.active = active

    def draw(self):

        icon_rect = shape.rectangle(0, 0, 64, 64)

        sprite_width = self.icon.width * 2
        sprite_offset = sprite_width / 2

        # transform to the icon position
        icon_rect.transform = mat3().translate(self.pos.x - 30, self.pos.y - 30)
        screen.pen = color.black
        screen.shape(icon_rect)

        icon_rect.transform = mat3().translate(self.pos.x - 32, self.pos.y - 32)
        screen.pen = color.light_grey
        screen.shape(icon_rect)

        if self.active:
            screen.pen = color.black
            screen.shape(icon_rect.stroke(2))

        # draw the icon sprite
        if sprite_width > 0:
            screen.blit(
                self.icon,
                rect(
                    self.pos.x - sprite_offset,
                    self.pos.y - 25,
                    sprite_width,
                    48
                )
            )


class Apps:
    def __init__(self, root):
        self.apps = []
        self.active_index = 0

        def capitalize(word):
            if len(word) <= 1:
                return word
            return word[0].upper() + word[1:]

        for path in sorted(os.listdir(root)):
            name = " ".join([capitalize(word) for word in path.split("_")])

            if is_dir(f"{root}/{path}"):
                if file_exists(f"{root}/{path}/icon.png"):
                    App(self.apps, name, path, image.load(f"{root}/{path}/icon.png"))

    @property
    def active(self):
        return self.apps[self.active_index]

    def activate(self, index):
        self.active_index = index
        for app in self.apps:
            app.activate(app.index == index)

    def draw_icons(self):
        offset = (self.active_index // 6) * 6
        for app in self.apps[offset:offset + 6]:
            app.draw()

    def draw_label(self):
        label = self.active.name
        w, _ = screen.measure_text(label)
        screen.pen = color.black
        screen.shape(shape.rectangle(cx - (w / 2) - 4, screen.height - 20, w + 8, 15, 4))
        screen.pen = color.white
        screen.text(label, cx - (w / 2), screen.height - 19)

    def draw_pagination(self, x=150, y=65):
        pages = math.ceil(len(self.apps) / 6)
        selected_page = self.active_index // 6
        y -= (pages * 7) / 2

        for page in range(pages):
            offset = page * 6
            pips = len(self.apps[offset:offset + 6])
            for pip in range(pips):
                if self.active_index - (page * 6) == pip:
                    screen.pen = color.rgb(255, 255, 255, 200)
                else:
                    screen.pen = color.rgb(255, 255, 255, 100) if page == selected_page else color.rgb(255, 255, 255, 50)
                screen.put(x + (pip % 3) * 2, y + (page * 7) + (pip // 3) * 2)

    def __len__(self):
        return len(self.apps)

    def __getitem__(self, i):
        return self.apps[i]
