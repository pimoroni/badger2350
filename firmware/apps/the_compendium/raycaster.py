import math

SCREEN_CENTRE_X = screen.width / 2
SCREEN_CENTRE_Y = screen.height / 2
PI_OVER_8 = math.pi / 8
TEXTURE_SIZE = 64


class RenderQueueItem:
    def __init__(self, x, y, grid_x, grid_y, distance, index, screen_x):
        self.x = x
        self.y = y
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.distance = distance
        self.index = index
        self.screen_x = screen_x


class RayIntersection(RenderQueueItem):
    def __init__(self, x, y, grid_x, grid_y, distance, index, screen_x, orientation, offset):
        super().__init__(x, y, grid_x, grid_y, distance, index, screen_x)
        self.orientation = orientation
        self.offset = offset


class MonsterSprite(RenderQueueItem):
    def __init__(self, x, y, grid_x, grid_y, distance, index, screen_x, sprite):
        super().__init__(x, y, grid_x, grid_y, distance, index, screen_x)
        self.sprite = sprite


def cast_ray(player, current_level, ray, rel_ray, ray_no, render_queue):
    # get the current cell of the player (and the current cell of the ray) from their position
    player_square_x = math.floor(player.x)
    player_square_y = math.floor(player.y)

    current_square_x = player_square_x
    current_square_y = player_square_y

    angle_scale_factor_x, angle_scale_factor_y = 1000, 1000

    # establish how many x the ray travels per y, and vice versa
    if ray.x != 0:
        angle_scale_factor_x = abs(1 / ray.x)

    if ray.y != 0:
        angle_scale_factor_y = abs(1 / ray.y)

    ray_length_x = 0
    ray_length_y = 0

    step_x = 1
    step_y = 1

    # establish the +- xy direction of the ray, and take the first step to the first x and y gridlines
    if ray.x < 0:
        step_x = -1
        ray_length_x = (player.x - current_square_x) * angle_scale_factor_x
    else:
        step_x = 1
        ray_length_x = ((current_square_x + 1) - player.x) * angle_scale_factor_x

    if ray.y < 0:
        step_y = -1
        ray_length_y = (player.y - current_square_y) * angle_scale_factor_y
    else:
        step_y = 1
        ray_length_y = ((current_square_y + 1) - player.y) * angle_scale_factor_y

    total_distance = 0

    i = 0
    while True:
        vertical = False
        orientation = 0

        # check if the distance to the nearest gridline is shorter in x or y,
        # then use the shorter to populate the intersection orientation.
        # this happens every step regardless of whether it hits something or not
        if ray_length_x < ray_length_y:
            current_square_x += step_x
            total_distance = ray_length_x
            ray_length_x += angle_scale_factor_x
            vertical = False
        else:
            current_square_y += step_y
            total_distance = ray_length_y
            ray_length_y += angle_scale_factor_y
            vertical = True

        if i > 10:
            break

        if current_square_x > current_level.map_width - 1 or current_square_x < 0:
            break

        if current_square_y > current_level.map_height - 1 or current_square_y < 0:
            break

        map_def_index = current_level.get_map_int(current_square_x, current_square_y)
        if map_def_index <= 0:  # check if the square we've just hit is empty, if so skip it
            continue

        distance = 0

        if vertical:
            if step_y == 1:
                orientation = 0  # step is used to determine if the ray is travelling in the +y or -y direction
            else:
                orientation = 2
        else:
            if step_x == 1:
                orientation = 3  # step is used to determine if the ray is travelling in the +x or -x direction
            else:
                orientation = 1

        pos_x = player.x + (ray.x * total_distance)
        pos_y = player.y + (ray.y * total_distance)

        # determine the u coordinate of the texture by looking at the part of the hit location after the decimal
        # the orientation of the wall determines whether it's the x or y part of the hit location
        if orientation == 0 or orientation == 2:
            offset = pos_x - current_square_x
        else:
            offset = pos_y - current_square_y

        screen_x = ray_no

        distance = 0

        # total_distance += math.cos(rel_ray[0])
        if vertical:
            distance = abs(ray_length_y - angle_scale_factor_y) * math.cos(rel_ray[0])
        else:
            distance = abs(ray_length_x - angle_scale_factor_x) * math.cos(rel_ray[0])

        render_queue.append(RayIntersection(pos_x, pos_y, current_square_x, current_square_y, distance, map_def_index, screen_x, orientation, offset))

        map_def = current_level.map_defs[map_def_index]
        if map_def.ray_end_point:
            break


def render_monster(monster, player, render_queue):
    rel_pos = vec2(monster.x - player.x, monster.y - player.y)
    dot_product = (rel_pos.x * player.x_vector) + (rel_pos.y * player.y_vector)
    if dot_product < 0:
        return

    cross_product = (rel_pos.y * player.x_vector) - (rel_pos.x * player.y_vector)

    view_angle = math.atan2(cross_product, dot_product)

    if abs(view_angle) > (player.fov / 2) + 0.1:
        return

    while view_angle > 2 * math.pi:
        view_angle -= 2 * math.pi
    while view_angle < -2 * math.pi:
        view_angle += 2 * math.pi

    x_pos = SCREEN_CENTRE_X - ((view_angle / (player.fov / 2)) * SCREEN_CENTRE_X)
    dist = math.sqrt(rel_pos.x ** 2 + rel_pos.y ** 2) * math.cos(view_angle)
    if dist > monster.radius:
        render_queue.append(MonsterSprite(monster.x, monster.y, monster.grid_x, monster.grid_y, dist, -2, x_pos, monster.sprite))


def draw_wall_slice(current_level, tilemap, ray_hit, y_scale):

    # cover our asses for /0 errors
    if ray_hit.distance == 0:
        wall_height = y_scale
    # wall height is inversely proportional to distance, simples
    else:
        wall_height = (screen.height * y_scale) / ray_hit.distance
    topend = SCREEN_CENTRE_Y - (wall_height / 2)

    u = ray_hit.offset

    if ray_hit.orientation == 2 or ray_hit.orientation == 3:
        u = 1.0 - u

    map_def = current_level.map_defs[ray_hit.index]
    v = map_def.texture - 1

    texture = tilemap.sprite(v, 0)

    brightness = int((ray_hit.distance / 10) * 128)
    if ray_hit.orientation == 0 or ray_hit.orientation == 2:
        brightness *= 2
    if brightness > 128:
        brightness = 128
    if brightness < 0:
        brightness = 0

    screen.pen = color.black

    screen.blit_vspan(texture, vec2(ray_hit.screen_x, topend), wall_height, vec2(u, 0.0), vec2(u, 1.0))


def draw_entity(ray_hit, y_scale):
    if ray_hit.distance == 0:
        size = screen.height
    else:
        size = (screen.height * y_scale) / ray_hit.distance

    x = ray_hit.screen_x - (size / 2)
    y = SCREEN_CENTRE_Y - (size / 2)
    w = size
    h = size
    screen.blit(ray_hit.sprite, rect(x, y, w, h))
