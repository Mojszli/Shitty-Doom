import pygame
import sys
import math

pygame.init()

WIDTH, HEIGHT = 800, 600
HALF_HEIGHT = HEIGHT // 2
FOV = math.pi / 3  
HALF_FOV = FOV / 2
TILE_SIZE = 64 
PLAYER_SPEED = 0.05
PLAYER_ROT_SPEED = 0.03

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
BROWN = (139, 69, 19)

WALL_COLORS = {
    1: (225, 225, 225)  

}
MAP = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1],
    [1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1],
    [1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

MAP_WIDTH = len(MAP[0])
MAP_HEIGHT = len(MAP)
RAY_COUNT = 320

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Updated Doom Walls")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

player_x = 1.5  
player_y = 1.5  
player_angle = 0  

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.is_alive = True
        
    def check_hit(self, x, y, radius=0.3):
        distance = math.sqrt((self.x - x)**2 + (self.y - y)**2)
        return distance < radius

enemies = [
    Enemy(3.5, 3.5),
    Enemy(5.5, 4.5),
    Enemy(2.5, 2.5),
    Enemy(4.5, 1.5)
]

score = 0

def create_wall_texture(wall_type, width, height):
    texture = pygame.Surface((width, height))
    base_color = WALL_COLORS.get(wall_type, (128, 128, 128))
    
    texture.fill(base_color)
    
    stripe_width = max(1, width // 8)
    for x in range(0, width, stripe_width * 2):
        darker_color = tuple(max(0, c - 30) for c in base_color)
        pygame.draw.rect(texture, darker_color, (x, 0, stripe_width, height))
    
    row_height = max(1, height // 12)
    for y in range(0, height, row_height):
        line_color = tuple(max(0, c - 20) for c in base_color)
        pygame.draw.line(texture, line_color, (0, y), (width, y), 1)
    
    for i in range(width * height // 20):
        x = pygame.math.Vector2(pygame.math.Vector2(0, width).x, pygame.math.Vector2(0, height).y)
        noise_color = tuple(min(255, max(0, c + pygame.math.Vector2(-10, 10).x)) for c in base_color)
        if 0 <= x.x < width and 0 <= x.y < height:
            texture.set_at((int(x.x), int(x.y)), noise_color)
    
    return texture

def cast_rays():
    rays = []
    for i in range(RAY_COUNT):
        ray_angle = player_angle - HALF_FOV + FOV * i / RAY_COUNT
        
        distance = 0
        hit_wall = False
        wall_type = 1
        hit_vertical = False  
        wall_x = 0  
        
        cos_a = math.cos(ray_angle)
        sin_a = math.sin(ray_angle)
        
        step_size = 0.01
        ray_x, ray_y = player_x, player_y
        
        while not hit_wall and distance < 20:
            distance += step_size
            ray_x = player_x + distance * cos_a
            ray_y = player_y + distance * sin_a
            
            if ray_x < 0 or ray_x >= MAP_WIDTH or ray_y < 0 or ray_y >= MAP_HEIGHT:
                hit_wall = True
                distance = 20  
                wall_type = 1
            elif MAP[int(ray_y)][int(ray_x)] != 0:
                hit_wall = True
                wall_type = MAP[int(ray_y)][int(ray_x)]
                
                prev_x = player_x + (distance - step_size) * cos_a
                prev_y = player_y + (distance - step_size) * sin_a
                
                if int(prev_x) != int(ray_x):
                    hit_vertical = True
                    wall_x = ray_y % 1
                else:
                    hit_vertical = False
                    wall_x = ray_x % 1

        distance = distance * math.cos(player_angle - ray_angle)
        
        wall_height = min(int(TILE_SIZE * 5 / distance), HEIGHT)
        
        wall_top = HALF_HEIGHT - wall_height // 2
        wall_bottom = wall_top + wall_height
        
        base_shade = max(40, min(255 - int(distance * 6), 255))
        
        if hit_vertical:
            shade = base_shade
        else:
            shade = int(base_shade * 0.75)
        
        rays.append({
            'distance': distance,
            'height': wall_height,
            'top': wall_top,
            'bottom': wall_bottom,
            'shade': shade,
            'wall_type': wall_type,
            'wall_x': wall_x,
            'hit_vertical': hit_vertical
        })
    
    return rays

def draw_scene(rays):
    screen.fill(BLACK)
    
    pygame.draw.rect(screen, DARK_GRAY, (0, HALF_HEIGHT, WIDTH, HALF_HEIGHT))
    
    ceiling_color = (30, 30, 60)
    pygame.draw.rect(screen, ceiling_color, (0, 0, WIDTH, HALF_HEIGHT))
    
    strip_width = WIDTH / RAY_COUNT
    
    for i, ray in enumerate(rays):
        x = i * strip_width
        
        base_color = WALL_COLORS.get(ray['wall_type'], (128, 128, 128))
        
        wall_color = tuple(int(c * ray['shade'] / 255) for c in base_color)
        
        pygame.draw.rect(screen, wall_color, (x, ray['top'], max(1, int(strip_width + 1)), ray['height']))
        
        if ray['height'] > 15 and strip_width > 1:
            noise_factor = (ray['wall_x'] * 31 + ray['distance']) % 1
            if noise_factor > 0.7:
                highlight_color = tuple(min(255, int(c * 1.15)) for c in wall_color)
            elif noise_factor < 0.3:
                shadow_color = tuple(int(c * 0.85) for c in wall_color)
                wall_color = shadow_color
            
            if ray['hit_vertical']:
                edge_color = tuple(min(255, int(c * 1.1)) for c in wall_color)
                if int(x) % 2 == 0:
                    pygame.draw.line(screen, edge_color, (x, ray['top']), (x, ray['top'] + ray['height']), 1)
            
            brick_pattern = int(ray['wall_x'] * 8) % 3
            if brick_pattern == 0 and ray['height'] > 30:
                mortar_color = tuple(int(c * 0.6) for c in base_color)
                for y_offset in range(0, ray['height'], max(8, ray['height'] // 8)):
                    if y_offset + ray['top'] < HEIGHT:
                        pygame.draw.line(screen, mortar_color, 
                                       (x, ray['top'] + y_offset), 
                                       (x + strip_width, ray['top'] + y_offset), 1)
    
    weapon_rect = pygame.Rect(WIDTH // 2 - 20, HEIGHT - 100, 40, 100)
    pygame.draw.rect(screen, BROWN, weapon_rect)
    
    pygame.draw.line(screen, WHITE, (WIDTH // 2 - 10, HEIGHT // 2), (WIDTH // 2 + 10, HEIGHT // 2), 2)
    pygame.draw.line(screen, WHITE, (WIDTH // 2, HEIGHT // 2 - 10), (WIDTH // 2, HEIGHT // 2 + 10), 2)
    
    for enemy in enemies:
        if not enemy.is_alive:
            continue
        
        dx = enemy.x - player_x
        dy = enemy.y - player_y
        
        enemy_angle = math.atan2(dy, dx)
        relative_angle = enemy_angle - player_angle
        
        while relative_angle > math.pi:
            relative_angle -= 2 * math.pi
        while relative_angle < -math.pi:
            relative_angle += 2 * math.pi
            
        if abs(relative_angle) < HALF_FOV:
            distance = math.sqrt(dx*dx + dy*dy)
            size = int(min(100, 800 / distance))
            
            screen_x = int(WIDTH // 2 + (relative_angle / HALF_FOV) * (WIDTH // 2) - size // 2)
            screen_y = int(HALF_HEIGHT - size // 2)
            
            if distance < 12:  
                pygame.draw.rect(screen, RED, (screen_x, screen_y, size, size))
    
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))
    
    enemies_left = sum(1 for enemy in enemies if enemy.is_alive)
    enemies_text = font.render(f"Enemies: {enemies_left}", True, WHITE)
    screen.blit(enemies_text, (10, 50))
    
    if enemies_left == 0:
        win_text = font.render("YOU WIN!", True, GREEN)
        screen.blit(win_text, (WIDTH // 2 - 80, HEIGHT // 2))

def check_collision(x, y):
    if x < 0 or x >= MAP_WIDTH or y < 0 or y >= MAP_HEIGHT:
        return True
    
    for i in range(int(y) - 1, int(y) + 2):
        for j in range(int(x) - 1, int(x) + 2):
            if 0 <= i < MAP_HEIGHT and 0 <= j < MAP_WIDTH:
                if MAP[i][j] != 0:
                    dist_x = abs(x - (j + 0.5))
                    dist_y = abs(y - (i + 0.5))
                    
                    if dist_x < 0.3 and dist_y < 0.3:
                        return True
    
    return False

def handle_shooting():
    global score
    
    mouse_pressed = pygame.mouse.get_pressed()
    
    if mouse_pressed[0]:
        cos_a = math.cos(player_angle)
        sin_a = math.sin(player_angle)
        
        for dist in range(1, 100):
            test_dist = dist * 0.1
            test_x = player_x + cos_a * test_dist
            test_y = player_y + sin_a * test_dist
            
            for enemy in enemies:
                if enemy.is_alive and enemy.check_hit(test_x, test_y):
                    enemy.is_alive = False
                    score += 100
                    return  
            
            if MAP[int(test_y)][int(test_x)] != 0:
                return

def main():
    global player_x, player_y, player_angle, score
    
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    player_x, player_y = 1.5, 1.5
                    player_angle = 0
                    score = 0
                    for enemy in enemies:
                        enemy.is_alive = True
            
        keys = pygame.key.get_pressed()
        
        move_speed = PLAYER_SPEED
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dx = math.cos(player_angle) * move_speed
            dy = math.sin(player_angle) * move_speed
            if not check_collision(player_x + dx, player_y + dy):
                player_x += dx
                player_y += dy
        
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dx = -math.cos(player_angle) * move_speed
            dy = -math.sin(player_angle) * move_speed
            if not check_collision(player_x + dx, player_y + dy):
                player_x += dx
                player_y += dy
        
        if keys[pygame.K_a]:
            dx = math.sin(player_angle) * move_speed
            dy = -math.cos(player_angle) * move_speed
            if not check_collision(player_x + dx, player_y + dy):
                player_x += dx
                player_y += dy
        
        if keys[pygame.K_d]:
            dx = -math.sin(player_angle) * move_speed
            dy = math.cos(player_angle) * move_speed
            if not check_collision(player_x + dx, player_y + dy):
                player_x += dx
                player_y += dy
        
        if keys[pygame.K_q]:
            player_angle -= PLAYER_ROT_SPEED
        
        if keys[pygame.K_e]:
            player_angle += PLAYER_ROT_SPEED
        
        player_angle %= 2 * math.pi
        
        handle_shooting()
        
        rays = cast_rays()
        draw_scene(rays)
        pygame.display.flip()
        
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()