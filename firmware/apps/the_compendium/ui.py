
ui_tex = SpriteSheet("assets/ui.png", 12, 1)

SCREEN_CENTRE_X = screen.width / 2


def draw_infobar(current_level, player, monsters):
    level_name = current_level.name
    level_text = "Currently in: {}".format(level_name)
    level_text_w, tex_h = screen.measure_text(level_text)
    level_top_left = SCREEN_CENTRE_X - (level_text_w / 2)
    level_backing = shape.rounded_rectangle(level_top_left - 2, 2, level_text_w + 4, 12, 3)

    lookat_text = None
    for monster in monsters:
        if monster.grid_x == player.lookat_x and monster.grid_y == player.lookat_y:
            lookat_text = "Looking at: {}".format(monster.name)

    if lookat_text is None:
        mapdef = current_level.get_map_def(player.lookat_x, player.lookat_y)
        lookat_text = "Looking at: {}".format(mapdef.name)

    lookat_text_w, tex_h = screen.measure_text(lookat_text)
    lookat_top_left = SCREEN_CENTRE_X - (lookat_text_w / 2)
    lookat_backing = shape.rounded_rectangle(lookat_top_left - 2, 16, lookat_text_w + 4, 12, 3)

    screen.pen = color.rgb(255, 255, 255, 160)
    screen.shape(level_backing)
    screen.shape(lookat_backing)

    screen.pen = color.black
    screen.text(level_text, vec2(level_top_left, 2))
    screen.text(lookat_text, vec2(lookat_top_left, 14))


def draw_map(current_level, player, monsters):
    screen.pen = color.white
    screen.rectangle(0, 0, 48, 48)
    screen.pen = color.black
    screen.rectangle(0, 0, 47, 47)
    screen.pen = color.white
    screen.rectangle(1, 1, 45, 45)
    screen.pen = color.black
    for j in range(-4, 5):
        for i in range(-4, 5):
            filled = False
            grid_x = i + player.grid_x
            grid_y = j + player.grid_y
            if grid_x < 0 or grid_x >= current_level.map_width or grid_y < 0 or grid_y >= current_level.map_height:
                filled = True
            else:
                grid_square = current_level.get_map_int(grid_x, grid_y)
                map_def = current_level.get_map_def(grid_x, grid_y)
                if grid_square >= 0 and not map_def.walkable:
                    filled = True

            if player.angle == 3:
                y = 21 - (5 * i)
                x = 21 - (5 * j)
            elif player.angle == 2:
                x = 21 - (5 * i)
                y = 21 + (5 * j)
            elif player.angle == 1:
                y = 21 + (5 * i)
                x = 21 + (5 * j)
            else:
                x = 21 + (5 * i)
                y = 21 - (5 * j)

            if filled:
                screen.rectangle(x, y, 5, 5)
                map_def = current_level.get_map_def(grid_x, grid_y)
                if map_def.interaction_class in (1, 4):
                    screen.pen = color.white
                    screen.rectangle(x + 1, y + 1, 3, 3)
                    screen.pen = color.black
                    screen.put(vec2(x + 2, y + 2))
            else:
                for monster in monsters:
                    if monster.grid_x == grid_x and monster.grid_y == grid_y:
                        screen.circle(x + 2, y + 2, 1.5)


    arrow = shape.custom([vec2(23, 19), vec2(26, 25), vec2(21, 25)])
    screen.shape(arrow)


def draw_buttons(current_level, player, monsters, gamepad):
    if gamepad:
        screen.blit(ui_tex.sprite(5, 0), vec2(0, 144))  # A button is always turn
        screen.blit(ui_tex.sprite(6, 0), vec2(32, 144))  # C button is always turn
        screen.blit(ui_tex.sprite(8, 0), vec2(216, 144))  # Up button is always inventory

        if player.can_walk(monsters):
            screen.blit(ui_tex.sprite(7, 0), vec2(16, 128))  # B button only appears if player can move forward
        else:
            screen.blit(ui_tex.sprite(9, 0), vec2(232, 128))  # Otherwise, magnifying glass

        lookat_item = player.get_lookat_item(current_level, monsters)
        if lookat_item.interaction_class == 1:
            screen.blit(ui_tex.sprite(10, 0), vec2(248, 144))
        elif lookat_item.interaction_class == 4:
            screen.blit(ui_tex.sprite(11, 0), vec2(248, 144))
    else:
        screen.blit(ui_tex.sprite(5, 0), vec2(41, 158))  # A button is always turn
        screen.blit(ui_tex.sprite(6, 0), vec2(206, 158))  # C button is always turn
        screen.blit(ui_tex.sprite(8, 0), vec2(246, 41))  # Up button is always inventory

        if player.can_walk(monsters):
            screen.blit(ui_tex.sprite(7, 0), vec2(124, 158))  # B button only appears if player can move forward
        else:
            screen.blit(ui_tex.sprite(9, 0), vec2(124, 158))  # Otherwise, magnifying glass

        lookat_item = player.get_lookat_item(current_level, monsters)
        if lookat_item.interaction_class == 1:
            screen.blit(ui_tex.sprite(10, 0), vec2(246, 124))
        elif lookat_item.interaction_class == 4:
            screen.blit(ui_tex.sprite(11, 0), vec2(246, 124))
