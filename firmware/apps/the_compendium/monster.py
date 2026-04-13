import math

import behaviours
import cutscene
import dialogue


class InteractionClass:
    SPEAK = 1
    EXAMINE = 2
    NONE = 3
    USE = 4

# The player is counted as a type of monster. Basically any monster (which includes npcs, static objects etc) acts like a player.
# Mostly unused in this game, as the NPCs here don't move around.
class Monster:
    def __init__(self, x, y, angle, details, player, level):
        fov, speed, radius, turn_speed, index, name, behaviour, spritesheet, interaction_class, interaction, description, examine_given = details
        self.x = x
        self.y = y
        self.fov = fov
        self.angle = angle
        self.speed = speed
        self.radius = radius
        self.turn_speed = turn_speed
        self.x_vector = 0
        self.y_vector = 0
        self.grid_x = math.floor(self.x)
        self.grid_y = math.floor(self.y)
        self.index = index
        self.sprite = None
        self.can_walk_x = True
        self.can_walk_y = True
        self.inventory = []
        self.lookat_x = 0
        self.lookat_y = 0
        self.name = name
        self.behaviour = behaviour
        self.behaviour.set_behaviour_target(self, self)
        self.spritesheet = spritesheet
        self.player = player
        self.level = level
        self.interaction_class = interaction_class
        self.interaction = interaction
        self.description = description
        self.examine_given = examine_given

    def update(self):
        if self.angle > 3:
            self.angle -= 4
        if self.angle < 0:
            self.angle += 4

        self.y_vector = 0
        self.x_vector = 0

        if self.angle == 0:
            self.y_vector = 1
        elif self.angle == 1:
            self.x_vector = -1
        elif self.angle == 2:
            self.y_vector = -1
        elif self.angle == 3:
            self.x_vector = 1

        self.grid_x = math.floor(self.x)
        self.grid_y = math.floor(self.y)

        inc_grid_x = self.grid_x + self.x_vector
        inc_grid_y = self.grid_y + self.y_vector
        self.lookat_x = int(inc_grid_x)
        self.lookat_y = int(inc_grid_y)

        if self.index < -1:
            self.update_sprite()

    def update_behaviour(self):
        self.behaviour.behaviour_update(self)

    def turn(self, direction):
        self.angle += direction
        self.check_movement([])
        self.update()

    def check_movement(self, monsters):
        self.update()

        inc_grid_x = self.grid_x + self.x_vector
        inc_grid_y = self.grid_y + self.y_vector

        if inc_grid_x > self.level.map_width - 1 or inc_grid_x < 0:
            return

        if inc_grid_y > self.level.map_height - 1 or inc_grid_y < 0:
            return

        self.can_walk_x = self.level.get_map_def(inc_grid_x, self.grid_y).walkable
        self.can_walk_y = self.level.get_map_def(self.grid_x, inc_grid_y).walkable

        for monster in monsters:
            if monster.grid_x == inc_grid_x and monster.grid_y == self.grid_y:
                self.can_walk_x = False
            if monster.grid_x == self.grid_x and monster.grid_y == inc_grid_y:
                self.can_walk_y = False

    def walk(self):
        if not self.can_walk_x and not self.can_walk_y:
            return

        new_pos_x = self.x + self.x_vector
        new_pos_y = self.y + self.y_vector
        new_grid_x = math.floor(new_pos_x)
        new_grid_y = math.floor(new_pos_y)

        if self.can_walk_x:
            self.x = new_pos_x
            self.grid_x = new_grid_x

        if self.can_walk_y:
            self.y = new_pos_y
            self.grid_y = new_grid_y

        self.update()

    def can_walk(self, monsters):
        self.check_movement(monsters)
        if self.angle == 0 or self.angle == 2:
            return self.can_walk_y
        return self.can_walk_x

    def interact(self):
        if self.interaction:
            return dialogue.dialogue_library[self.interaction]
        return None

    def examine(self):
        return cutscene.StatusMessage(self.description, self.examine_given)

    # Returns whatever's in the sprite ahead of the monster from its point of view.
    def get_lookat_item(self, current_level, monsters):
        self.update()
        for monster in monsters:
            if monster.grid_x == self.lookat_x and monster.grid_y == self.lookat_y:
                return monster

        return current_level.get_map_def(self.lookat_x, self.lookat_y)

    # If the monster's texture is an 8-way sprite sheet, this delivers the right sprite according to
    # its angle to the player. Otherwise just delivers the single sprite.
    def update_sprite(self):
        if isinstance(self.spritesheet, SpriteSheet):
            rel_pos = vec2(self.player.x - self.x, self.player.y - self.y)
            dot_product = (rel_pos.x * self.x_vector) + (rel_pos.y * self.y_vector)
            cross_product = (rel_pos.y * self.x_vector) - (rel_pos.x * self.y_vector)
            view_angle = math.atan2(cross_product, dot_product)
            texture = math.floor(((view_angle + math.pi) / (2 * math.pi)) * 7)
            self.sprite = self.spritesheet.sprite(texture, 0)
        else:
            self.sprite = self.spritesheet

    def add_inventory(self, items):
        for item in items:
            if item not in self.inventory:
                self.inventory.append(item)

    def rem_inventory(self, items):
        for item in items:
            if item in self.inventory:
                self.inventory.remove(item)

# Finally all the monster data, graphics then definitions.
column = image.load("assets/column.png")
solderbeard = image.load("assets/solderbeard.png")
monstera = image.load("assets/monstera.png")
monkey = image.load("assets/monkey.png")
robot = image.load("assets/robot.png")
barrel = image.load("assets/barrel.png")
ninja = image.load("assets/ninja.png")

monster_db = {
    1: (1.0472, 0.5, 0.3, math.pi / 20, -1, "Player", behaviours.Behaviour, column, InteractionClass.NONE, None, "", []),
    2: (math.pi / 4, 0.25, 0.7, math.pi / 20, -2, "Pillar", behaviours.FreezeBehaviour, column, InteractionClass.EXAMINE, None, "Doric? Or Ionic? I can never remember.", []),
    3: (math.pi / 4, 0.25, 0.7, math.pi / 20, -3, "Solderbeard", behaviours.FreezeBehaviour, solderbeard, InteractionClass.SPEAK, "sb_greeting", "He's probably nicer than he smells.", []),
    4: (math.pi / 4, 0.25, 0.7, math.pi / 20, -2, "Monstera", behaviours.FreezeBehaviour, monstera, InteractionClass.EXAMINE, None, "Aah! Monsters! Oh no, wait, autocorrect. Aah! Monstera!", []),
    5: (math.pi / 4, 0.25, 0.7, math.pi / 20, -3, "Monkey", behaviours.FreezeBehaviour, monkey, InteractionClass.SPEAK, "mk_greeting", "It's like the mange has become its own separate life form.", []),
    6: (math.pi / 4, 0.25, 0.7, math.pi / 20, -3, "Barrel", behaviours.FreezeBehaviour, barrel, InteractionClass.EXAMINE, None, "Why is it always barrels in places like this?", []),
    7: (math.pi / 4, 0.25, 0.7, math.pi / 20, -3, "Robot", behaviours.FreezeBehaviour, robot, InteractionClass.SPEAK, "rb_greeting", "Should she be making that noise? I can smell smoke.", []),
    8: (math.pi / 4, 0.25, 0.7, math.pi / 20, -3, "Ninja", behaviours.FreezeBehaviour, ninja, InteractionClass.SPEAK, "nj_greeting", "He's utterly motionless. Does... does he think I can't see him?", [])
}


# Inventory items are included here too, they just hold a few pieces of data
class inventory_item:
    def __init__(self, id, text, tangible_status, hidden):
        self.id = id
        self.text = text
        self.tangible_status = tangible_status
        self.hidden = hidden


item_db = {
    "banana": inventory_item("banana", "A surprisingly fresh, ripe banana.", True, False),
    "battery": inventory_item("battery", "A battery, the explodey kind.", True, False),
    "body_pillow": inventory_item("body_pillow", "A body pillow with an anime girl on it.", True, False),
    "comic_book": inventory_item("comic_book", "A rather tattered Dora Daring comic.", True, False),
    "mk_quest": inventory_item("mk_quest", "Monkey wants you to find his lost comic book.", False, False),
    "nj_awake": inventory_item("nj_awake", "You've gained Ninja's attention.", False, False),
    "nj_meet": inventory_item("nj_meet", "unlocks ninja interactions for other npcs", False, True),
    "nj_name": inventory_item("nj_name", "unlocks teasing the ninja about the ancient dojo", False, True),
    "note_ninjasnack": inventory_item("note_ninjasnack", "Ninja can be easily distracted with snacks.", False, False),
    "note_robotpatch": inventory_item("note_robotpatch", "Robot used Ninja's scroll to patch a leak.", False, False),
    "pocky": inventory_item("pocky", "A box of sweet little biscuity treats.", True, False),
    "small_label": inventory_item("small_label", "A little label made of stiff card.", True, False),
    "unlock_mk_accusation": inventory_item("unlock_mk_accusation", "Ninja says that Monkey took his wall scroll.", False, False),
    "unlock_mk_whatplace": inventory_item("unlock_mk_whatplace", "unlocks whatplace dialogue for monkey", False, True),
    "unlock_mk_whytalk": inventory_item("unlock_mk_whytalk", "unlocks whytalk dialogue for monkey", False, True),
    "unlock_nj_hello": inventory_item("unlock_nj_hello", "unlocks hello dialogue for ninja", False, True),
    "unlock_nj_whatplace2": inventory_item("unlock_nj_whatplace2", "unlocks teasing the ninja with ninja_name", False, True),
    "unlock_rb_rundown": inventory_item("unlock_rb_rundown", "unlocks the rundown dialogue for robot", False, True),
    "unlock_sb_name": inventory_item("unlock_sb_name", "unlocks name dialogue for solderbeard", False, True),
    "unlock_sb_whatplace": inventory_item("unlock_sb_whatplace", "unlocks whatplace dialogue for solderbeard", False, True),
    "wall_scroll": inventory_item("wall_scroll", "A wall scroll with a recipe scrawled on the back.", True, False),
    "meatloaf_recipe": inventory_item("meatloaf_recipe", "You have Uncle Jared's meatloaf recipe.", False, False),
}
