import math
import os
import random
import sys
import time


sys.path.insert(0, "/system/apps/the_compendium")
os.chdir("/system/apps/the_compendium")
import cutscene
import dialogue
import level
import monster
import raycaster
import ui
import qwstpad

badge.mode(FAST_UPDATE)

standard_font = pixel_font.load("/system/assets/fonts/sins.ppf")
screen.font = standard_font
screen.antialias = image.OFF

game_state = 0

title = image.load("assets/title.png")
game_over = image.load("assets/game_over.png")
ui_tex_unit = SpriteSheet("assets/ui.png", 12, 1)
ui_tex_pad = SpriteSheet("assets/ui_pad.png", 12, 1)
ui_tex = ui_tex_unit

background = None
tilemap = None

player = None
monsters = []
rays = []
ray_vectors = []
render_queue = []
Y_SCALE = 0.7
previous_screen = 0
current_level = None
gamepad = None
controls={}

# Setting up default values for the first run, and loading in the state with the
# user choices if the file's there.
state = {
    "player_x": None,
    "player_y": None,
    "player_angle": 0,
    "player_inventory": ["unlock_nj_hello"],
    "current_level": "lobby",
    "previous_screen": None,
    "game_state": 0
}

State.load("the_compendium", state)
if state["previous_screen"]:
    previous_screen = dialogue.dialogue_library[state["previous_screen"]]
print(state["game_state"])
game_state = state["game_state"]


# This changes the current level to the provided one, loads in texture and background images and
# kicks off initialising the player and NPCs.
def init_level(new_level, transition, entry_point, angle):
    global current_level, background, tilemap, state

    current_level = level.levels[new_level]
    background = image.load(f"assets/{current_level.id}_bg.png")
    tilemap = SpriteSheet(f"assets/{current_level.textures}.png", 16, 1)

    init_player(transition, entry_point, angle)
    init_monsters()


# This finds the player start points in the level, sets the player's position to the specified one and
# updates their position for the raycaster.
def init_player(transition, entry_point, angle):
    global player
    start_pos_list = level.find_entity(current_level, -1)
    player_pos = start_pos_list[entry_point] if entry_point < len(start_pos_list) else start_pos_list[0]

    if player is None:
        x = player_pos.x if state["player_x"] is None else state["player_x"]
        y = player_pos.y if state["player_y"] is None else state["player_y"]
        player = monster.Monster(x, y, 0, monster.monster_db[1], vec2(1, 1), current_level)
        player.inventory = state["player_inventory"]
        init_raycast()
        player.angle = int(state["player_angle"])

    elif transition:
        player.x = player_pos.x
        player.y = player_pos.y
        player.angle = angle

    player.level = current_level
    player.update()
    update_player_rays()


# This searches the level map for monster IDs, then spawns the appropriate monster / prop / npc at each.
def init_monsters():
    monsters.clear()
    for entity in range(2, len(monster.monster_db) + 1):
        map_monsters = level.find_entity(current_level, -entity)
        for map_monster in map_monsters:
            new_monster = monster.Monster(map_monster.x, map_monster.y, random.randint(0, 3), monster.monster_db[entity], player, current_level)
            new_monster.update()
            monsters.append(new_monster)


# This sets up a field of rays according to the player FOV. Done once at the start to avoid doing
# expensive trig functions hundreds of times each update.
def init_raycast():
    global rays
    num_rays = screen.width
    rayStep = player.fov / num_rays
    rayAngle = player.angle - (player.fov / 2)
    temp_rays = []
    for _ in range(num_rays):
        ray_x = math.cos(rayAngle)
        ray_y = math.sin(rayAngle)
        temp_rays.insert(0, (rayAngle, vec2(ray_x, ray_y)))
        rayAngle += rayStep
    rays = temp_rays


def init_gamepad():
    global gamepad
    gamepads = qwstpad.Gamepadhelper()
    for i in gamepads.pads:
        if i is not None:
            gamepad = i
            return i
    return None


def parse_controls():
    global controls, gamepad, ui_tex

    if not gamepad:
        gamepad = init_gamepad()

    if gamepad:
        try:
            gamepad.update_buttons()
        except OSError:
            gamepad = init_gamepad()

    if gamepad:
        controls["LEFT"] = gamepad.held("L")
        controls["RIGHT"] = gamepad.held("R")
        controls["WALK"] = gamepad.held("U")
        controls["EXAMINE"] = gamepad.held("X")
        controls["INTERACT"] = gamepad.held("A")
        controls["INVENTORY"] = gamepad.held("Y")
        controls["ANY"] = gamepad.held()
        controls["DIALOG1"] = gamepad.held("A")
        controls["DIALOG2"] = gamepad.held("B")
        controls["DIALOG3"] = gamepad.held("X")
        controls["DIALOG4"] = gamepad.held("Y")
        controls["DIALOG5"] = gamepad.held("+")
        ui_tex = ui_tex_pad
    else:
        controls["LEFT"] = badge.pressed(BUTTON_A)
        controls["RIGHT"] = badge.pressed(BUTTON_C)
        controls["WALK"] = badge.pressed(BUTTON_B)
        controls["EXAMINE"] = badge.pressed(BUTTON_B)
        controls["INTERACT"] = badge.pressed(BUTTON_DOWN)
        controls["INVENTORY"] = badge.pressed(BUTTON_UP)
        controls["ANY"] = badge.pressed()
        controls["DIALOG1"] = badge.pressed(BUTTON_A)
        controls["DIALOG2"] = badge.pressed(BUTTON_B)
        controls["DIALOG3"] = badge.pressed(BUTTON_C)
        controls["DIALOG4"] = badge.pressed(BUTTON_DOWN)
        controls["DIALOG5"] = badge.pressed(BUTTON_UP)
        ui_tex = ui_tex_unit


# Takes the rays defined above and generates a series of vectors for their directions,\# rotated by the player's angle.
def update_player_rays():
    ray_vectors.clear()
    for ray in rays:
        ray_x = (player.x_vector * ray[1].x) - (player.y_vector * ray[1].y)
        ray_y = (player.y_vector * ray[1].x) + (player.x_vector * ray[1].y)
        ray_vectors.append(vec2(ray_x, ray_y))


# Renders the 2.5D of the scene. It casts rays, finds wall distance and puts it all in a render queue. Then does the same with monsters
# in the player's FOV. Then it orders the render queue in reverse order of distance, and renders everything from back
# to front. Overdrawing is only done where necessary.
def render_scene():
    global render_queue, Y_SCALE
    screen.blit(background, rect(0, 0, screen.width, screen.height))

    for ray_no in range(len(ray_vectors)):
        ray = ray_vectors[ray_no]
        rel_ray = rays[ray_no]
        raycaster.cast_ray(player, current_level, ray, rel_ray, ray_no, render_queue)

    for m in monsters:
        raycaster.render_monster(m, player, render_queue)

    render_queue.sort(key=lambda x: x.distance, reverse=True)

    for ray_hit in render_queue:
        if isinstance(ray_hit, raycaster.RayIntersection):
            raycaster.draw_wall_slice(current_level, tilemap, ray_hit, Y_SCALE)
        elif isinstance(ray_hit, raycaster.MonsterSprite):
            raycaster.draw_entity(ray_hit, Y_SCALE)

    render_queue = []


# Initialising the level - if there was a saved state it's going to take its data from that, otherwise
# This is for the initial start position.
init_level(state["current_level"], False, 2, 0)


# Updates the behaviour of all monsters and NPCs. Doesn't do anything in this version as they don't move.
def monster_move():
    for m in monsters:
        m.update_behaviour()
        m.update()


# Processes button commands for the player.
def player_move():
    global y_factor

    if previous_screen is None:
        if controls["LEFT"]:
            player.turn(1)
            return None
        if controls["RIGHT"]:
            player.turn(-1)
            return None
        if gamepad:
            if controls["WALK"]:
                player.check_movement(monsters)
                if player.can_walk(monsters):
                    player.walk()
                    return None
            if controls["EXAMINE"]:
                lookat_item = player.get_lookat_item(current_level, monsters)
                if lookat_item is None:
                    return None
                return lookat_item.examine()
        else:
            if controls["WALK"]:
                player.check_movement(monsters)
                if player.can_walk(monsters):
                    player.walk()
                    return None
                lookat_item = player.get_lookat_item(current_level, monsters)
                if lookat_item is None:
                    return None
                return lookat_item.examine()
        if controls["INTERACT"]:
            lookat_item = player.get_lookat_item(current_level, monsters)
            return lookat_item.interact()
        if controls["INVENTORY"]:
            return cutscene.InventoryScreen(player)
    return None


# The series of commands needed to get the 3D scene on screen and dithered.
def draw_3d():
    update_player_rays()
    render_scene()
    screen.dither()


# Self explanatory, drawing the UI
def draw_ui():
    ui.draw_buttons(current_level, player, monsters, gamepad)
    ui.draw_infobar(current_level, player, monsters)
    ui.draw_map(current_level, player, monsters)


# Saves the state of the game ready for the next refresh.
def save_state():
    global state, player

    state["player_x"] = player.x
    state["player_y"] = player.y
    state["player_angle"] = player.angle
    state["player_inventory"] = player.inventory
    state["current_level"] = current_level.id
    if isinstance(previous_screen, dialogue.DialogueNode):
        state["previous_screen"] = previous_screen.id
    else:
        state["previous_screen"] = None

    State.save("the_compendium", state)

init_gamepad()

def update():
    global previous_screen, state, game_state

    parse_controls()

    # If we're on the title screen, just display it.
    if game_state == 0:
        screen.blit(title, vec2(0, 0))
        if controls["ANY"]:
            game_state = 1
            state["game_state"] = 1
            save_state()

    # If we're playing...
    elif game_state == 1:
        # If nothing else is specified to draw by the previous_screen variable, this will draw the
        # 3D scene. Otherwise...

        # If the last screen was dialogue, find out what was chosen
        if isinstance(previous_screen, dialogue.DialogueNode):
            if controls["DIALOG1"]:
                previous_screen = previous_screen.choose(0)
            elif controls["DIALOG2"]:
                previous_screen = previous_screen.choose(1)
            elif controls["DIALOG3"]:
                previous_screen = previous_screen.choose(2)
            elif controls["DIALOG4"]:
                previous_screen = previous_screen.choose(3)
            elif controls["DIALOG5"]:
                previous_screen = previous_screen.choose(4)

        # If we're in the inventory, the only thing to do is come out of the inventory.
        elif isinstance(previous_screen, cutscene.InventoryScreen):
            previous_screen = None

        # If we're already on the 3D scene, process the controls.
        else:
            monster_move()
            previous_screen = player_move()

        # If what was chosen in dialogue or by interacting with an NPC was more dialogue, show it
        if isinstance(previous_screen, dialogue.DialogueNode):
            msg = None
            if len(previous_screen.given_item) > 0:
                player.add_inventory(previous_screen.given_item)
                for item in previous_screen.given_item:
                    if not monster.item_db[item].hidden:
                        msg = cutscene.InDialogueMessage("Received item.")
            if len(previous_screen.removed_item) > 0:
                player.rem_inventory(previous_screen.removed_item)
            draw_3d()
            previous_screen.draw(player, standard_font, ui_tex)
            if msg:
                msg.draw()

        # Otherwise if it was a level transition, init that new level
        elif isinstance(previous_screen, dialogue.LevelSelectNode):
            init_level(previous_screen.level_id, True, previous_screen.entry_point, previous_screen.angle)
            msg = None

            if len(previous_screen.removed_item) > 0:
                player.rem_inventory(previous_screen.removed_item)

            if len(previous_screen.given_item) > 0:
                player.add_inventory(previous_screen.given_item)
                for item in previous_screen.given_item:
                    if not monster.item_db[item].hidden:
                        msg = cutscene.StatusMessage("Received item.")
            else:
                previous_screen = None
            draw_3d()
            draw_ui()
            if msg:
                msg.draw()

        # Or if it was a status message, display the 3D  scene then the message
        elif isinstance(previous_screen, cutscene.StatusMessage):
            draw_3d()
            draw_ui()
            previous_screen.draw()
            if previous_screen.removed_item is not None:
                if len(previous_screen.removed_item) > 0:
                    player.rem_inventory(previous_screen.removed_item)
            if previous_screen.given_item is not None:
                if len(previous_screen.given_item) > 0:
                    player.add_inventory(previous_screen.given_item)
                    for item in previous_screen.given_item:
                        if not monster.item_db[item].hidden:
                            previous_screen = cutscene.StatusMessage("Received item.")
                else:
                    previous_screen = None

        # If the inventory button was pressed, show the inventory
        elif isinstance(previous_screen, cutscene.InventoryScreen):
            previous_screen.draw(player)

        # Or if it was the endgame, just display the end screen.
        elif isinstance(previous_screen, dialogue.ExitNode):
            screen.blit(game_over, vec2(0, 0))
            game_state = 2

        # Otherwise draw the 3D scene.
        else:
            draw_3d()
            draw_ui()

        save_state()  # This is called every update no matter what, or it would forget everything between refreshes.

    # Finally if it's the end of the game, reset everything back to starting conditions.
    elif game_state == 2:
        state = {
            "player_x": None,
            "player_y": None,
            "player_angle": 0,
            "player_inventory": ["unlock_nj_hello"],
            "current_level": "lobby",
            "previous_screen": None,
            "game_state": 0
        }
        State.save("the_compendium", state)

    # Update the screen
    badge.update()

    timer = time.ticks_ms()

    while gamepad and not gamepad.pressed():
        parse_controls()
        if time.ticks_ms() - timer >= 60000:
            badge.sleep()

    if not gamepad:
        wait_for_button_or_alarm(timeout=60000)


run(update)
