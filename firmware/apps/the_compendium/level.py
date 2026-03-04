import cutscene
import dialogue


class InteractionClass:
    SPEAK = 1
    EXAMINE = 2
    NONE = 3
    USE = 4

# Level contains the basic info about its dimensions, its layout of course and basic methods to get what integer or map definition is in the map layout at given coordinates.
class Level:
    def __init__(self, id, layout, name, textures, map_defs):
        self.layout = layout
        self.name = name
        self.map_defs = map_defs
        self.map_width = len(self.layout)
        self.map_height = len(self.layout[0])
        self.id = id
        self.textures = textures

    def get_map_def(self, x, y):
        if x < 0 or x >= self.map_width or y < 0 or y >= self.map_height:
            return self.map_defs[0]

        if self.layout[x][y] < 0:
            return self.map_defs[0]
        return self.map_defs[self.layout[x][y]]

    def get_map_int(self, x, y):
        if x < 0 or x >= self.map_width or y < 0 or y >= self.map_height:
            return self.map_defs[0]

        return self.layout[x][y]


# Map definitions are for a particular tile, they specify details such as whether it's solid, what texture to use etcetera.
class MapDef:
    def __init__(self, texture, walkable, ray_end_point, name, interaction_class, interaction, description, examine_given):
        self.texture = texture
        self.walkable = walkable
        self.ray_end_point = ray_end_point
        self.name = name
        self.interaction_class = interaction_class
        self.interaction = interaction
        self.description = description
        self.examine_given = examine_given

    def interact(self):
        if self.interaction:
            return dialogue.dialogue_library[self.interaction]
        return None

    def examine(self):
        return cutscene.StatusMessage(self.description, self.examine_given)


# For a given entity number, returns a list of coordinates for evey appearance of that entity in the map.
def find_entity(current_level, entity_id):
    # search the map for the specified entity
    found = []
    for i in range(current_level.map_width):
        for j in range(current_level.map_height):
            if current_level.get_map_int(i, j) == entity_id:
                found.append(vec2(i + 0.5, j + 0.5))
    return found


# Finally the actual data for the game's levels.
# x+ is up, y+ is right. Player 0 angle faces y+.
lobby_gamemap = [
            [1, 1, 7, 1, 3, 1, 1],
            [1,-2,-1,-2,-1,-2, 1],
            [5,-1, 0, 6, 0,-1, 4],
            [1,-2,-3,-2,-1,-2, 1],
            [1, 1, 1, 1, 2, 1, 1]
            ]

storage_gamemap = [
            [ 8,  9,  9,  9,  9,  8],
            [ 8,  9, 18, 10,  0,  8],
            [ 8, 10,  0,  0,  9,  8],
            [11, -1,  0,  0, 10,  8],
            [ 8,  8,  8,  8,  8,  8]
            ]

jungle_gamemap = [
            [12, 12, 13, 12, 12, 12, 12],
            [12, 12, 16,  0,  0, 16, 12],
            [12, 12, 17, 14, 15,  0, 13],
            [12, 13, -4, -4,  0,  0, 13],
            [12, 12,  0, 15, -5,  0, 12],
            [14, -1,  0,  0,  0,  0, 12],
            [12, 12,  0, -4,  0, 17, 12],
            [12, 12,  0,  0, 15,  0, 12],
            [12, 13, 16,  0,  0, -4, 12],
            [12, 12, 13, 13, 12, 12, 12]
            ]

spaceport_gamemap = [
            [ 1,  1,  2,  3,  1,  1],
            [ 2,  5, -6, -6,  0,  2],
            [ 1,  0,  0, -6,  0,  1],
            [ 3,  0,  0,  0,  0,  3],
            [ 4, -1,  0,  0, -7,  3],
            [ 3,  0,  0,  0,  0,  1],
            [ 2,  6,  7,  0,  0,  2],
            [ 1,  6,  6,  0,  0,  1],
            [ 1,  2,  1,  3,  2,  1]
            ]

dojo_gamemap = [
            [ 8,  8,  9,  8,  9,  8,  8],
            [ 8,  0,  0,  0,  0,  0,  9],
            [ 9,  0,  0,  0,  0,  0, 10],
            [11, -1,  0, -8,  0,  0,  9],
            [ 9,  0,  0,  0,  0,  0, 10],
            [ 8,  0,  0,  0,  0,  0,  9],
            [ 8,  8,  9,  8,  9,  8,  8]
            ]


# MapDef parameters: texture in library, walkable, opaque, name
mapDefs1 = {
    0: MapDef(0, True, False, "Nothing", InteractionClass.NONE, None, "", []),
    1: MapDef(1, False, True, "Stonework", InteractionClass.EXAMINE, None, "Seems to be well-worn gritstone", []),
    2: MapDef(2, False, True, "Bamboo doorway", InteractionClass.USE, "enter_dojo", "The legend above the door says 'To the Cloud Fortress", []),
    3: MapDef(3, False, True, "Heavy steel doorway", InteractionClass.USE, "enter_spaceport", "This looks like an airlock door.", []),
    4: MapDef(4, False, True, "Hole", InteractionClass.USE, "enter_jungle", "These look like jungle plants growing out of this hole. I think I could fit through.", []),
    5: MapDef(5, False, True, "Note", InteractionClass.EXAMINE, None, "The label says 'Please do not read this label.' That's odd. I'll hang onto it.", ["small_label"]),
    6: MapDef(6, True, False, "Compendium sign", InteractionClass.NONE, None, "", []),
    7: MapDef(7, False, False, "Door", InteractionClass.USE, "enter_storage", "This door's fairly boring compared to the others. Just says STORAGE.", []),
    8: MapDef(8, False, True, "Brickwork", InteractionClass.EXAMINE, None, "Brick. Gosh, it's exciting.", []),
    9: MapDef(9, False, True, "Wooden crates", InteractionClass.EXAMINE, None, "These are labelled with all sorts of labels. Throwing stars, bananas... they seem well stocked.", []),
    10: MapDef(10, False, False, "Small crates", InteractionClass.EXAMINE, None, "This one's just marked BOOTY.", []),
    11: MapDef(7, False, False, "Door", InteractionClass.USE, "exit_storage", "Looks like the door back to the lobby.", []),
    12: MapDef(11, False, True, "Dense jungle", InteractionClass.EXAMINE, None, "No way I can get through this thick jungle.", []),
    13: MapDef(12, False, True, "Dense jungle", InteractionClass.EXAMINE, None, "No way I can get through this thick jungle.", []),
    14: MapDef(4, False, True, "Hole", InteractionClass.USE, "exit_jungle", "It's the hole back through to the lobby.", []),
    15: MapDef(13, False, False, "Jungle plants", InteractionClass.NONE, None, "No way I can get through this thick jungle.", []),
    16: MapDef(14, False, False, "Jungle plants", InteractionClass.NONE, None, "No way I can get through this thick jungle.", []),
    17: MapDef(15, False, False, "Jungle plants", InteractionClass.NONE, None, "No way I can get through this thick jungle.", []),
    18: MapDef(16, False, True, "Pillow crate", InteractionClass.USE, "open_crate", "Is this crate entirely filled with anime body pillows?", []),
}

mapDefs2 = {
    0: MapDef(0, True, False, "Nothing", InteractionClass.NONE, None, "", []),
    1: MapDef(1, False, True, "Panelling", InteractionClass.EXAMINE, None, "Scuffed faux-plastic wall plating.", []),
    2: MapDef(2, False, True, "Panelling", InteractionClass.EXAMINE, None, "Scuffed faux-plastic wall plating.", []),
    3: MapDef(3, False, True, "Light panel", InteractionClass.EXAMINE, None, "I didn't know it was possible for light to get sick, but what this panel is putting out is very ill indeed.", []),
    4: MapDef(4, False, True, "Airlock door", InteractionClass.USE, "exit_spaceport", "That's the airlock back to the lobby.", []),
    5: MapDef(5, False, False, "Chain link fence", InteractionClass.EXAMINE, None, "Utterly impregnable.", []),
    6: MapDef(6, False, True, "Mecha-crates", InteractionClass.EXAMINE, None, "They're crates. But SPACE!.", []),
    7: MapDef(7, False, False, "Small mecha-crates", InteractionClass.EXAMINE, None, "Smaller crates. Like the bigger ones, they're SPACE!.", []),
    8: MapDef(8, False, True, "Wood panelling", InteractionClass.EXAMINE, None, "A tricky diagnosis, but in my expert opinion... wood.", []),
    9: MapDef(9, False, True, "Wall scroll", InteractionClass.EXAMINE, None, "I don't think this kanji means what he thinks it means.", []),
    10: MapDef(10, False, True, "Incredible view", InteractionClass.EXAMINE, None, "This mountain top is incredible! I didn't think they'd have the budget to show this on a Pico.", []),
    11: MapDef(11, False, True, "Fortress door", InteractionClass.USE, "exit_dojo", "That's the door back to the lobby.", []),
}

levels = {
"lobby": Level("lobby", lobby_gamemap, "Lobby", "wall_tex", mapDefs1),
"storage": Level("storage", storage_gamemap, "Storage", "wall_tex", mapDefs1),
"jungle": Level("jungle", jungle_gamemap, "The Jungle", "wall_tex", mapDefs1),
"spaceport": Level("spaceport", spaceport_gamemap, "Space Station Zeta", "wall_tex_2", mapDefs2),
"dojo": Level("dojo", dojo_gamemap, "Cloud Fortress", "wall_tex_2", mapDefs2),
}
