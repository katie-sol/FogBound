#Add libraries here

#Declare your main driver function here

#Additional functions go here
import random
import pygame
import sys
import math

# map
TILE_SIZE = 16
MAP_W = 80   # tiles
MAP_H = 50   # tiles
SCREEN_W = 800
SCREEN_H = 600
ROOM_MAX_SIZE = 12
ROOM_MIN_SIZE = 5
MAX_ROOMS = 15
# LEVEL SYSTEM
current_level = 1
max_levels = 3
enemies_per_level = 3

# COLORS
COLOR_WALL = (50, 50, 60)
COLOR_FLOOR = (200, 200, 200)
COLOR_PLAYER = (255, 220, 80)
COLOR_BG = (10, 10, 20)
COLOR_UNSEEN = (0, 0, 0)
COLOR_VISITED = (30, 30, 40)
COLOR_CORRIDOR = (170, 170, 170)

# TILE TYPES
WALL = 0
FLOOR = 1
ENEMY = 2
COLOR_ENEMY=(200,50,50)
ENEMY_MOVE_COOLDOWN = 50

# HP
player_hp = 6
MAX_HP = 6

# Animation Timers
damage_animation_timer = 0
screen_flash_timer = 0
shake_timer = 0

class PowerUp:
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.type = type  # 'health', 'speed', 'shield', 'range', 'fov'
        self.active = True

    def draw(self, screen, cam):
        px = (self.x - cam[0]) * TILE_SIZE
        py = (self.y - cam[1]) * TILE_SIZE

        # Background square

        # Draw icon based on type
        if self.type == 'health':
            # Red heart
            pygame.draw.polygon(screen, (255,0,0), [(px+4, py+8), (px+8, py+12), (px+12, py+8), (px+8, py+4)])
            pygame.draw.circle(screen, (255,0,0), (px+5, py+6), 3)
            pygame.draw.circle(screen, (255,0,0), (px+11, py+6), 3)

        elif self.type == 'speed':
            # Blue lightning
            pygame.draw.polygon(screen, (0,200,255), [(px+6, py+2), (px+10, py+2), (px+6, py+8), (px+10, py+8), (px+4, py+14), (px+8, py+8), (px+4, py+8)])

        elif self.type == 'range':
            # Yellow arrow pointing up
            pygame.draw.polygon(screen, (255,255,0), [(px+8, py+2), (px+12, py+10), (px+10, py+10), (px+10, py+14), (px+6, py+14), (px+6, py+10), (px+4, py+10)])

        elif self.type == 'fov':
            # Purple eye
            pygame.draw.ellipse(screen, (200,0,255), (px+4, py+6, 8, 4))
            pygame.draw.circle(screen, (255,255,255), (px+8, py+8), 1)



def spawn_powerups_random(game_map, rooms, count=5):
    powerups = []
    for _ in range(count):
        while True:
            room = random.choice(rooms)
            x = random.randint(room.x1+1, room.x2-2)
            y = random.randint(room.y1+1, room.y2-2)
            if game_map[x][y] == FLOOR:
                type = random.choice(['health','speed','range','fov'])
                powerups.append(PowerUp(x, y, type))
                break
    return powerups

def spawn_powerup_on_enemy_death(enemy):
    if random.random() < 0.35:  # 35% drop chance
        type = random.choice(['health','speed','range','fov'])
        return PowerUp(enemy[0], enemy[1], type)
    return None

def apply_powerup(player_x, player_y, powerups, player_state):
    for powerup in powerups:
        if powerup.active and player_x == powerup.x and player_y == powerup.y:
            if powerup.type == 'health':
                player_state['hp'] = min(player_state['max_hp'], player_state['hp'] + 1)
            elif powerup.type == 'speed':
                player_state['speed'] *= 1.1
                player_state['speed_timer'] = pygame.time.get_ticks()
            elif powerup.type == 'range':
                player_state['attack_range'] += 1
                player_state['range_timer'] = pygame.time.get_ticks()
            elif powerup.type == 'fov':
                player_state['fov_radius'] += 2
                player_state['fov_timer'] = pygame.time.get_ticks()
            powerup.active = False


class RectRoom:
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
    def center(self):
        cx = (self.x1 + self.x2) // 2
        cy = (self.y1 + self.y2) // 2
        return (cx, cy)
    def intersects(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)
def make_map():
    #Create the walls
    game_map = [[WALL for y in range(MAP_H)] for x in range(MAP_W)]
    rooms = []
    for r in range(MAX_ROOMS):
        w = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x = random.randint(1, MAP_W - w - 2)
        y = random.randint(1, MAP_H - h - 2)
        new_room = RectRoom(x, y, w, h)

        #Checking for overlap
        failed = False
        for other in rooms:
            if new_room.intersects(other):
                failed = True
                break

        if not failed:
            #Make rooms
            for i in range(new_room.x1, new_room.x2):
                for j in range(new_room.y1, new_room.y2):
                    game_map[i][j] = FLOOR

            if rooms:
                #Connect rooms with corridors
                (prev_x, prev_y) = rooms[-1].center()
                (new_x, new_y) = new_room.center()
                if random.randint(0,1) == 1:
                    horiz_corridor(game_map, prev_x, new_x, prev_y)
                    vert_corridor(game_map, prev_y, new_y, new_x)
                else:
                    vert_corridor(game_map, prev_y, new_y, prev_x)
                    horiz_corridor(game_map, prev_x, new_x, new_y)

            rooms.append(new_room)

    return game_map, rooms

#create horizontal corridors
def horiz_corridor(game_map, x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2)+1):
        if 0 <= x < MAP_W and 0 <= y < MAP_H:
            game_map[x][y] = FLOOR

#create vertical corridors
def vert_corridor(game_map, y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2)+1):
        if 0 <= x < MAP_W and 0 <= y < MAP_H:
            game_map[x][y] = FLOOR

#determine player start
def player_start(rooms, game_map):
    if rooms:
        return rooms[0].center()
    for x in range(MAP_W):
        for y in range(MAP_H):
            if game_map[x][y] == FLOOR:
                return (x, y)

def spawn_enemies(game_map, rooms, count=10):
    enemies=[]
    for x in range(count):
        room=random.choice(room[1:]) if len(rooms)>1 else rooms[0]
        x=random.randint(room.x1 + 1, room.x2 - 2)
        y=random.randint(room.y1 + 1, room.y2 -2)
# spawn_enemies updated:
def spawn_enemies(game_map, rooms, level=1, enemies_per_level=3):
    enemies = []
    count = enemies_per_level + (level - 1) * 2  # base +2 per level

    for _ in range(count):
        room = random.choice(rooms[1:]) if len(rooms) > 1 else rooms[0]
        x = random.randint(room.x1 + 1, room.x2 - 2)
        y = random.randint(room.y1 + 1, room.y2 - 2)

        if game_map[x][y] == FLOOR:
            enemies.append([x, y])

    return enemies, game_map
#draw map for visuals
def draw_map(surface, game_map, visible, visited, camera, enemies, powerups):
    cam_x, cam_y = camera
    tiles_x = SCREEN_W // TILE_SIZE
    tiles_y = SCREEN_H // TILE_SIZE

    for sx in range(tiles_x): # sx = Screen X
        for sy in range(tiles_y): # sy = Screen y
            x = cam_x + sx
            y = cam_y + sy
            px = sx * TILE_SIZE #px = Player X - py = Player y
            py = sy * TILE_SIZE

            if 0 <= x < MAP_W and 0 <= y < MAP_H:
                if not visited[x][y]:
                    pygame.draw.rect(surface, COLOR_UNSEEN, (px, py, TILE_SIZE, TILE_SIZE))
                else:
                    if not visible[x][y]:
                        pygame.draw.rect(surface, COLOR_VISITED, (px, py, TILE_SIZE, TILE_SIZE))
                        if game_map[x][y] == FLOOR:
                            pygame.draw.rect(surface, COLOR_CORRIDOR, (px+3, py+3, TILE_SIZE-6, TILE_SIZE-6))
                    else:
                        if game_map[x][y] == FLOOR:
                            pygame.draw.rect(surface, COLOR_FLOOR, (px, py, TILE_SIZE, TILE_SIZE))
                            for ex, ey in enemies:
                                if ex==x and ey==y:
                                    pygame.draw.rect(surface, COLOR_ENEMY, (px + 2, py + 4, TILE_SIZE - 4, TILE_SIZE - 4))
                                    pygame.draw.rect(surface, (150, 0, 0), (px + 4, py, TILE_SIZE - 8, 4))
                                    pygame.draw.circle(surface, (255,255,255), (px + 5, py + 2), 1)
                                    pygame.draw.circle(surface, (255,255,255), (px + TILE_SIZE - 5, py + 2), 1)
                                    pygame.draw.line(surface, (100,0,0), (px + 2, py), (px + 3, py - 2), 1)
                                    pygame.draw.line(surface, (100,0,0), (px + TILE_SIZE - 3, py), (px + TILE_SIZE - 4, py - 2), 1)
                            for powerup in powerups:
                                if powerup.active and powerup.x == x and powerup.y == y:
                                    powerup.draw(surface, (0,0))
                        else:
                            pygame.draw.rect(surface, COLOR_WALL, (px, py, TILE_SIZE, TILE_SIZE))
            else:
                pygame.draw.rect(surface, COLOR_UNSEEN, (px, py, TILE_SIZE, TILE_SIZE))

#determine fov
def fov(game_map, px, py, radius=8):
    visible = [[False for y in range(MAP_H)] for x in range(MAP_W)]
    for x in range(max(0, px-radius), min(MAP_W, px+radius+1)):
        for y in range(max(0, py-radius), min(MAP_H, py+radius+1)):
            dx = x - px
            dy = y - py
            if dx*dx + dy*dy <= radius*radius:
                visible[x][y] = True
    return visible
def move_enemies(enemies, game_map, player_x, player_y, player_hp, damage_animation_timer, screen_flash_timer, shake_timer, player_damage_cooldown, DAMAGE_COOLDOWN_TIME ):
    updated = []
    occupied = set()

    for (ex, ey) in enemies:

        # Default wandering movement
        dx, dy = random.choice([
            (1,0), (-1,0), (0,1), (0,-1), (0,0)
        ])

        # Player detection (simple vision range)
        vision_range = 7
        if abs(ex - player_x) + abs(ey - player_y) <= vision_range:
            dx = 0 if ex == player_x else (1 if player_x > ex else -1)
            dy = 0 if ey == player_y else (1 if player_y > ey else -1)

        nx = ex + dx
        ny = ey + dy

        # Check if next spot is the player or adjacent

        # Prevent moving into walls or other enemies
        if not (0 <= nx < MAP_W and 0 <= ny < MAP_H and game_map[nx][ny] == FLOOR) or (nx, ny) in occupied:
            nx, ny = ex, ey

        occupied.add((nx, ny))
        updated.append([nx, ny])

    return updated, player_hp, damage_animation_timer, screen_flash_timer, shake_timer, player_damage_cooldown

#add fog of war for added difficulty
def camera(px, py):
    tiles_x = SCREEN_W // TILE_SIZE
    tiles_y = SCREEN_H // TILE_SIZE
    cam_x = px - tiles_x // 2
    cam_y = py - tiles_y // 2
    cam_x = max(0, min(MAP_W - tiles_x, cam_x))
    cam_y = max(0, min(MAP_H - tiles_y, cam_y))
    return cam_x, cam_y

def draw_heart(surface, x, y, state="full", size=16):
    color_full = (255, 80, 90)
    color_empty = (60, 60, 60)
    color_half = (255, 140, 150)

    if state == "empty":
        color = color_empty
    elif state == "half":
        color = color_half
    else:
        color = color_full

    r = size // 2

    pygame.draw.circle(surface, color, (x + r//2, y + r//2), r)
    pygame.draw.circle(surface, color, (x + r + r//2, y + r//2), r)

    pygame.draw.polygon(surface, color, [
        (x, y + r),
        (x + size, y + r),
        (x + size//2, y + size)
    ])

    if state == "half":
        pygame.draw.rect(surface, (0,0,0), (x + size//2, y, size//2, size+2))

def draw_player_preview(screen, px, py, size=TILE_SIZE):
    scale = size / TILE_SIZE
    rect_w = (TILE_SIZE - 6) * scale
    rect_h = (TILE_SIZE - 6) * scale
    pygame.draw.rect(screen, (255, 220, 80), (px + 3*scale, py + 4*scale, rect_w, rect_h))
    pygame.draw.rect(screen, (255, 200, 150), (px + 4*scale, py, (TILE_SIZE - 8)*scale, 4*scale))
    eye_y = py + 2*scale
    eye_x_offset = rect_w * 0.25
    pygame.draw.circle(screen, (0, 0, 0), (int(px + 3*scale + eye_x_offset), int(eye_y)), max(1, int(scale)))
    pygame.draw.circle(screen, (0, 0, 0), (int(px + 3*scale + rect_w - eye_x_offset), int(eye_y)), max(1, int(scale)))
    pygame.draw.line(screen, (255, 220, 80), (px, py + 5*scale), (px + 3*scale, py + 5*scale), max(1, int(scale)))
    pygame.draw.line(screen, (255, 220, 80), (px + TILE_SIZE - 3*scale, py + 5*scale), (px + TILE_SIZE, py + 5*scale), max(1, int(scale)))
    pygame.draw.line(screen, (150, 150, 150), (px + TILE_SIZE - 1*scale, py + 2*scale), (px + TILE_SIZE - 1*scale, py + TILE_SIZE - 2*scale), max(1, int(scale)))


def draw_enemy_preview(screen, px, py, size=TILE_SIZE):
    scale = size / TILE_SIZE
    rect_w = (TILE_SIZE - 4) * scale
    rect_h = (TILE_SIZE - 4) * scale
    pygame.draw.rect(screen, COLOR_ENEMY, (px + 2*scale, py + 4*scale, rect_w, rect_h))
    pygame.draw.rect(screen, (150, 0, 0), (px + 4*scale, py, (TILE_SIZE - 8)*scale, 4*scale))
    eye_y = py + 2*scale
    eye_x_offset = rect_w * 0.25
    pygame.draw.circle(screen, (255, 255, 255), (int(px + 2*scale + eye_x_offset), int(eye_y)), max(1, int(scale)))
    pygame.draw.circle(screen, (255, 255, 255), (int(px + 2*scale + rect_w - eye_x_offset), int(eye_y)), max(1, int(scale)))
    horn_height = 2 * scale
    horn_x_offset = rect_w * 0.2
    pygame.draw.line(screen, (100, 0, 0), (px + 2*scale + horn_x_offset, py), (px + 2*scale + horn_x_offset + scale, py - horn_height), max(1, int(scale)))
    pygame.draw.line(screen, (100, 0, 0), (px + 2*scale + rect_w - horn_x_offset, py), (px + 2*scale + rect_w - horn_x_offset - scale, py - horn_height), max(1, int(scale)))



def take_damage(player_state, damage_animation_timer, screen_flash_timer, shake_timer):
    if player_state.get('shield', False):
        player_state['shield'] = False  # absorb one hit
    else:
        player_state['hp'] -= 1
        damage_animation_timer = 15
        screen_flash_timer = 8
        shake_timer = 6
    return damage_animation_timer, screen_flash_timer, shake_timer, player_state


def reset_game():
    game_map, rooms = make_map()
    player_x, player_y = rooms[0].center() if rooms else (MAP_W//2, MAP_H//2)

    enemies = []
    for _ in range(8):
        room = random.choice(rooms)
        ex = random.randint(room.x1 + 1, room.x2 - 2)
        ey = random.randint(room.y1 + 1, room.y2 - 2)
        enemies.append([ex, ey])

    visited = [[False for y in range(MAP_H)] for x in range(MAP_W)]

    player_hp = 5
    player_max_hp = 5
    damage_animation_timer = 0
    screen_flash_timer = 0
    shake_timer = 0
    enemy_timer = 0
    attack_timer = 0
    attacking = False
    player_damage_cooldown = 0  # frames until player can take damage again
    player_state = {
        'hp': player_hp,
        'max_hp': player_max_hp,
        'speed': 1.0,
        'speed_timer': 0,
        'shield': False,
        'attack_range': 2,
        'range_timer': 0,
        'fov_radius': 8,
        'fov_timer': 0,
        'attack_circle_radius': TILE_SIZE * 1.2
        }



    return (game_map, rooms, player_x, player_y, enemies, visited,
            player_hp, player_max_hp, damage_animation_timer,
            screen_flash_timer, shake_timer, enemy_timer, attack_timer, attacking,
            player_damage_cooldown, player_state)
class MagicParticle:
    def __init__(self, x, y, dx, dy, lifetime=10):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.lifetime = lifetime
        self.size = random.randint(3, 6)
        self.color = (random.randint(120, 180), random.randint(120, 220), 255)

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.lifetime -= 1

    def draw(self, screen, cam):
        px = int((self.x - cam[0]) * TILE_SIZE)
        py = int((self.y - cam[1]) * TILE_SIZE)

        pygame.draw.circle(screen, self.color, (px, py), self.size)


def create_magic_attack(px, py, attack_range):
    particles = []
    for i in range(20):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.1, 0.3)
        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed
        lifetime = random.randint(8, 14)
        particles.append(MagicParticle(px, py, dx, dy, lifetime=random.randint(8, 14)))

    return particles


def main():
    global current_level
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Procedural Dungeon")
    clock = pygame.time.Clock()

    move_delay = 150
    home_screen = True
    font_title = pygame.font.SysFont(None, 48)
    font_option = pygame.font.SysFont(None, 32)
    # Default selections
    difficulty_options = ["Easy", "Medium", "Hard"]
    difficulty_index = 0
    levels_options = [1, 2, 3, 4, 5]
    levels_index = 2  # default 3 levels
    magic_particles = []


    while home_screen:
        screen.fill(COLOR_BG)

        # Title
        font_title = pygame.font.SysFont(None, 48)
        title_text = font_title.render("PROCEDURAL DUNGEON", True, (255, 255, 255))
        screen.blit(title_text, ((SCREEN_W - title_text.get_width()) // 2, SCREEN_H // 5))
        # Difficulty
        font_option = pygame.font.SysFont(None, 32)
        diff_text = font_option.render(f"Difficulty: {difficulty_options[difficulty_index]}", True, (200, 200, 200))
        screen.blit(diff_text, ((SCREEN_W - diff_text.get_width()) // 2, SCREEN_H // 2 - 30))
        # Levels
        level_text = font_option.render(f"Levels: {levels_options[levels_index]}", True, (200, 200, 200))
        screen.blit(level_text, ((SCREEN_W - level_text.get_width()) // 2, SCREEN_H // 2 + 30))
        # Instructions
        instr_text = font_option.render("Use LEFT/RIGHT for Difficulty, UP/DOWN for Levels, ENTER to start", True, (150, 150, 150))
        screen.blit(instr_text, ((SCREEN_W - instr_text.get_width()) // 2, SCREEN_H // 2 + 100))
        draw_player_preview(screen, 50, SCREEN_H-100 , size=80)          # bottom-left
        draw_enemy_preview(screen, SCREEN_W - 114, SCREEN_H-100, size=80)  
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                # Difficulty selection
                if event.key == pygame.K_LEFT:
                    difficulty_index = (difficulty_index - 1) % len(difficulty_options)
                if event.key == pygame.K_RIGHT:
                    difficulty_index = (difficulty_index + 1) % len(difficulty_options)
            
                # Level selection
                if event.key == pygame.K_UP:
                    levels_index = (levels_index - 1) % len(levels_options)
                if event.key == pygame.K_DOWN:
                    levels_index = (levels_index + 1) % len(levels_options)

                # Start game
                if event.key == pygame.K_RETURN:
                    home_screen = False

    # Set variables based on selection
    if difficulty_options[difficulty_index] == "Easy":
        enemies_per_level = 3
    elif difficulty_options[difficulty_index] == "Medium":
        enemies_per_level = 5
    else:
        enemies_per_level = 8

    max_levels = levels_options[levels_index]
    current_level = 1

    while True:
        (
            game_map, rooms, player_x, player_y, enemies, visited,
            player_hp, player_max_hp, damage_animation_timer,
            screen_flash_timer, shake_timer, enemy_timer,
            attack_timer, attacking, player_damage_cooldown, player_state
        ) = reset_game()

        running = True
        fov_radius = 8
        time_since_move = 0
        last_move = (0, -1)   # default facing up
        DAMAGE_COOLDOWN_TIME = 15
        enemies, game_map = spawn_enemies(game_map, rooms, current_level, enemies_per_level)
        powerups = spawn_powerups_random(game_map, rooms, count=5)


        while running:
            # UPDATE PARTICLES
            for p in magic_particles[:]:
                p.update()
                if p.lifetime <= 0:
                    magic_particles.remove(p)
            Tickrate = clock.tick(60)
            if player_damage_cooldown > 0:
                player_damage_cooldown -= 1
            if damage_animation_timer > 0:
                damage_animation_timer -= 1
            if screen_flash_timer > 0:
                screen_flash_timer -= 1
            if shake_timer > 0:
                shake_timer -= 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    return

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        return

                    if event.key == pygame.K_r:
                        (
                            game_map, rooms, player_x, player_y, enemies, visited,
                            player_hp, player_max_hp, damage_animation_timer,
                            screen_flash_timer, shake_timer, enemy_timer
                        ) = reset_game()

                    if event.key == pygame.K_SPACE and not attacking:
                            attacking = True

                            # determine direction
                            if last_move == (0, -1):  
                                direction = "up"
                            elif last_move == (0, 1): 
                                direction = "down"
                            elif last_move == (-1, 0): 
                                direction = "left"
                            else: 
                                direction = "right"

                            # spawn particles
                            magic_particles += create_magic_attack(
                            player_x + 0.5,   # center of tile
                            player_y + 0.5,   # center of tile
                            player_state['attack_range'],
                            )
                    attack_timer = 10
  


            # MOVEMENT
            time_since_move += Tickrate
            keys = pygame.key.get_pressed()
            movey = 0
            movex = 0

            if time_since_move >= move_delay:
                if keys[pygame.K_UP] or keys[pygame.K_w]:
                    movey -= 1
                if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    movey += 1
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    movex -= 1
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    movex += 1

                if movex != 0 and movey != 0:
                    movey = 0

                currentx = player_x + movex
                currenty = player_y + movey

                if game_map[currentx][currenty] == FLOOR:
                    player_x = currentx
                    player_y = currenty

                time_since_move = 0

                # enemy movement
                enemy_timer += Tickrate
               # if enemy_timer >= ENEMY_MOVE_COOLDOWN:
                   # enemies = move_enemies(enemies, game_map, player_x, player_y)
                    # enemy_timer = 0

                if enemy_timer >= ENEMY_MOVE_COOLDOWN:
                    enemies, player_hp, damage_animation_timer, screen_flash_timer, shake_timer, player_damage_cooldown = move_enemies(
                        enemies, game_map, player_x, player_y,
                        player_hp, damage_animation_timer, screen_flash_timer, shake_timer,
                        player_damage_cooldown, DAMAGE_COOLDOWN_TIME
                    )
                    enemy_timer = 0




 
            # DAMAGE CHECK 
            for ex, ey in enemies: 
                if abs(ex - player_x) <= 1 and abs(ey - player_y) <= 1: 
                    if player_damage_cooldown <= 0:
                        damage_animation_timer, screen_flash_timer, shake_timer, player_state = take_damage(
                            player_state, damage_animation_timer, screen_flash_timer, shake_timer
                        )
                        player_damage_cooldown = DAMAGE_COOLDOWN_TIME
                    if player_state['hp'] <= 0:
                        print("You died!") 
                        pygame.time.delay(1000) 
                        pygame.quit()
                        sys.exit()  

            # ATTACK LOGIC
            if attacking and attack_timer > 0:
                attack_radius = player_state['attack_range']
                new_enemy_list = []
                for ex, ey in enemies:
                    dx = ex - player_x
                    dy = ey - player_y
                    if dx*dx + dy*dy <= attack_radius*attack_radius:
                        powerup = spawn_powerup_on_enemy_death([ex, ey])
                        if powerup:
                            powerups.append(powerup)
                        continue
                    new_enemy_list.append([ex, ey])
                enemies = new_enemy_list

                attack_timer -= 1
                if attack_timer <= 0:
                    attacking = False
            # --- LEVEL COMPLETION ---
            if len(enemies) == 0:
                if current_level < max_levels:
                    current_level += 1
                    enemies, game_map = spawn_enemies(game_map, rooms, current_level)
                    print(f"--- LEVEL {current_level} START ---")
                else:
                    print("YOU WIN! GAME OVER")
                    pygame.time.delay(2000)
                    pygame.quit()
                    sys.exit()

            apply_powerup(player_x, player_y, powerups, player_state)
            player_hp = player_state['hp']  # sync for display
            fov_radius = player_state['fov_radius']


            # FOV
            visible = fov(game_map, player_x, player_y, fov_radius)

            for x in range(MAP_W):
                for y in range(MAP_H):
                    if visible[x][y]:
                        visited[x][y] = True

            cam = camera(player_x, player_y)
            cam_x, cam_y = cam

            shake_offset_x = 0
            shake_offset_y = 0

            if shake_timer > 0:
                shake_offset_x = random.randint(-3, 3)
                shake_offset_y = random.randint(-3, 3)

            screen.fill(COLOR_BG)
            draw_map(screen, game_map, visible, visited, cam, enemies, powerups)

            for p in magic_particles:
                p.draw(screen, cam)


            for powerup in powerups:
                if powerup.active:
                    powerup.draw(screen, cam)

            # draw player
            px = (player_x - cam[0]) * TILE_SIZE + shake_offset_x
            py = (player_y - cam[1]) * TILE_SIZE + shake_offset_y
            pygame.draw.rect(screen, (255, 220, 80), (px + 3, py + 4, TILE_SIZE - 6, TILE_SIZE - 6))
            pygame.draw.rect(screen, (255, 200, 150), (px + 4, py, TILE_SIZE - 8, 4))
            pygame.draw.circle(screen, (0, 0, 0), (px + 5, py + 2), 1)
            pygame.draw.circle(screen, (0, 0, 0), (px + TILE_SIZE - 5, py + 2), 1)
            pygame.draw.line(screen, (255, 220, 80), (px, py + 5), (px + 3, py + 5), 2)
            pygame.draw.line(screen, (255, 220, 80), (px + TILE_SIZE - 3, py + 5), (px + TILE_SIZE, py + 5), 2)
            pygame.draw.line(screen, (150, 150, 150), (px + TILE_SIZE - 1, py + 2), (px + TILE_SIZE - 1, py + TILE_SIZE - 2), 2)


            # red flash overlay
            if screen_flash_timer > 0:
                flash_surface = pygame.Surface((SCREEN_W, SCREEN_H))
                flash_surface.set_alpha(120)
                flash_surface.fill((255, 0, 0))
                screen.blit(flash_surface, (0, 0))

            # HP
            heart_x = 10
            heart_y = 10
            hp = player_hp

            for i in range(player_max_hp):
                if hp >= 1:
                    draw_heart(screen, heart_x, heart_y, "full")
                    hp -= 1
                elif hp > 0:
                    draw_heart(screen, heart_x, heart_y, "half")
                    hp = 0
                else:
                    draw_heart(screen, heart_x, heart_y, "empty")

                heart_x += 22

            # Enemy remaining counter
            enemy_text = pygame.font.SysFont(None, 24).render(f"Enemies Remaining: {len(enemies)}", True, (255, 255, 255))
            screen.blit(enemy_text, (10, 40))
            # Current level counter
            level_text = pygame.font.SysFont(None, 24).render(f"Current Level: {current_level}", True, (255, 255, 255))
            screen.blit(level_text, (SCREEN_W - 150, 10))       


            pygame.display.flip()    
        pygame.quit()




if __name__ == "__main__":
    main()