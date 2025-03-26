import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import time
import sys
import pywavefront
import random

# Initialize Pygame and OpenGL
pygame.init()
display = (800, 600)
pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
glTranslatef(0.0, 0.0, -10)

# Initialize Pygame mixer for sound effects and music
try:
    pygame.mixer.init()
    print("Pygame mixer initialized successfully.")
    pygame.mixer.set_num_channels(16)  # Increase the number of channels to 16
except pygame.error as e:
    print(f"Failed to initialize Pygame mixer: {e}")

# Load sound effects
try:
    shoot_sound = pygame.mixer.Sound('shoot.wav')  # Load shooting sound
    explosion_sound = pygame.mixer.Sound('explosion.wav')  # Load explosion sound
    # Set volume (0.0 to 1.0)
    shoot_sound.set_volume(0.5)
    explosion_sound.set_volume(0.5)
    print("Sound effects loaded successfully.")
except FileNotFoundError:
    print("Sound files not found! Please add 'shoot.wav' and 'explosion.wav' to the directory.")
    shoot_sound = None
    explosion_sound = None
except pygame.error as e:
    print(f"Failed to load sound files: {e}")
    shoot_sound = None
    explosion_sound = None

# Load background music
try:
    pygame.mixer.music.load('background_music.wav')  # Load background music
    pygame.mixer.music.set_volume(0.3)  # Set music volume
    pygame.mixer.music.play(-1)  # Play music on loop (-1 for infinite loop)
    print("Background music loaded and playing.")
except FileNotFoundError:
    print("Background music file not found! Please add 'background_music.wav' to the directory.")
except pygame.error as e:
    print(f"Failed to load background music: {e}")

# Load enemy model (if you have one, otherwise we'll use a custom design)
try:
    enemy_model = pywavefront.Wavefront('mech.obj', collect_faces=True)
except FileNotFoundError:
    enemy_model = None

# Player and enemy positions
player_pos = [0, 0, 0]  # x, y, z (player stays at z=0)
player_rotation = [0, 0, 0]  # pitch, yaw, roll
player_velocity = [0, 0, 0]  # For smooth movement
player_health = 3  # Player starts with 3 health points
enemies = []  # List of enemy positions [x, y, z]
enemy_speed = 0.01
bullets = []  # List to store player bullets
enemy_bullets = []  # List to store enemy bullets
explosions = []  # List to store explosion particles
power_ups = []  # List to store power-ups
score = 0  # Player score

# Game state
game_over = False
game_active = True

# Terrain segments
terrain_segments = [
    {'base_z': 0, 'current_z': 0},
    {'base_z': -20, 'current_z': -20},
    {'base_z': -40, 'current_z': -40}
]
terrain_speed = 0.1
terrain_features = {segment['base_z']: [] for segment in terrain_segments}

# Draw a simplified Arwing
def draw_arwing(pos, rotation, scale=0.5):
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glRotatef(rotation[0], 1, 0, 0)
    glRotatef(rotation[1], 0, 1, 0)
    glRotatef(rotation[2], 0, 0, 1)
    glScalef(scale, scale, scale)

    glBegin(GL_TRIANGLES)
    glColor3f(1, 1, 1)
    glVertex3f(0, 0, 2)
    glVertex3f(-0.5, 0, 0)
    glVertex3f(0.5, 0, 0)

    glVertex3f(0, 0.3, 0)
    glVertex3f(-0.5, 0, 0)
    glVertex3f(0.5, 0, 0)

    glVertex3f(0, -0.3, 0)
    glVertex3f(-0.5, 0, 0)
    glVertex3f(0.5, 0, 0)

    glVertex3f(0, 0.3, 0)
    glVertex3f(0, -0.3, 0)
    glVertex3f(-0.5, 0, -1)
    glVertex3f(0, 0.3, 0)
    glVertex3f(0, -0.3, 0)
    glVertex3f(0.5, 0, -1)
    glEnd()

    glBegin(GL_TRIANGLES)
    glColor3f(1, 1, 1)
    glVertex3f(-0.5, 0, 0)
    glVertex3f(-3, -0.5, 0)
    glVertex3f(-0.5, 0, -1)

    glVertex3f(0.5, 0, 0)
    glVertex3f(3, -0.5, 0)
    glVertex3f(0.5, 0, -1)

    glColor3f(0, 0, 1)
    glVertex3f(-3, -0.5, 0)
    glVertex3f(-2, -0.5, 0)
    glVertex3f(-2, -0.5, -0.5)

    glVertex3f(3, -0.5, 0)
    glVertex3f(2, -0.5, 0)
    glVertex3f(2, -0.5, -0.5)
    glEnd()

    glBegin(GL_QUADS)
    glColor3f(0, 0, 1)
    vertices = [
        (-0.6, 0, -1), (-0.6, 0.1, -1), (-0.4, 0.1, -1), (-0.4, 0, -1),
        (-0.6, 0, -1.2), (-0.6, 0.1, -1.2), (-0.4, 0.1, -1.2), (-0.4, 0, -1.2),
        (-0.6, 0, -1), (-0.6, 0.1, -1), (-0.6, 0.1, -1.2), (-0.6, 0, -1.2),
        (-0.4, 0, -1), (-0.4, 0.1, -1), (-0.4, 0.1, -1.2), (-0.4, 0, -1.2),
        (-0.6, 0.1, -1), (-0.6, 0.1, -1.2), (-0.4, 0.1, -1.2), (-0.4, 0.1, -1),
        (-0.6, 0, -1), (-0.6, 0, -1.2), (-0.4, 0, -1.2), (-0.4, 0, -1)
    ]
    for i in range(0, len(vertices), 4):
        for vertex in vertices[i:i+4]:
            glVertex3fv(vertex)

    vertices = [
        (0.4, 0, -1), (0.4, 0.1, -1), (0.6, 0.1, -1), (0.6, 0, -1),
        (0.4, 0, -1.2), (0.4, 0.1, -1.2), (0.6, 0.1, -1.2), (0.6, 0, -1.2),
        (0.4, 0, -1), (0.4, 0.1, -1), (0.4, 0.1, -1.2), (0.4, 0, -1.2),
        (0.6, 0, -1), (0.6, 0.1, -1), (0.6, 0.1, -1.2), (0.6, 0, -1.2),
        (0.4, 0.1, -1), (0.4, 0.1, -1.2), (0.6, 0.1, -1.2), (0.6, 0.1, -1),
        (0.4, 0, -1), (0.4, 0, -1.2), (0.6, 0, -1.2), (0.6, 0, -1)
    ]
    for i in range(0, len(vertices), 4):
        for vertex in vertices[i:i+4]:
            glVertex3fv(vertex)
    glEnd()

    glPopMatrix()

# Draw a simple cube (used for terrain objects, bullets, enemies, and explosion particles)
def draw_cube(pos, size=0.5, color=(1, 1, 1)):
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glBegin(GL_QUADS)
    glColor3f(*color)
    vertices = [
        (size, -size, -size), (size, size, -size), (-size, size, -size), (-size, -size, -size),
        (size, -size, size), (size, size, size), (-size, size, size), (-size, -size, size),
        (-size, -size, -size), (-size, size, -size), (-size, size, size), (-size, -size, size),
        (size, -size, -size), (size, size, -size), (size, size, size), (size, -size, size),
        (-size, size, -size), (size, size, -size), (size, size, size), (-size, size, size),
        (-size, -size, -size), (size, -size, -size), (size, -size, size), (-size, -size, size)
    ]
    for i in range(0, len(vertices), 4):
        for vertex in vertices[i:i+4]:
            glVertex3fv(vertex)
    glEnd()
    glPopMatrix()

# Draw a simplified TIE Fighter (Star Wars enemy ship)
def draw_tie_fighter(pos, scale=1.0):
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glScalef(scale, scale, scale)

    # Cockpit (central sphere approximated as a cube)
    draw_cube([0, 0, 0], size=0.5, color=(0.3, 0.3, 0.3))  # Dark gray for the cockpit

    # Cockpit window (small green square on the front)
    glBegin(GL_QUADS)
    glColor3f(0, 1, 0)  # Green for the cockpit window
    window_size = 0.2
    glVertex3f(-window_size, -window_size, -0.5 - 0.01)  # Slightly in front of the cockpit
    glVertex3f(window_size, -window_size, -0.5 - 0.01)
    glVertex3f(window_size, window_size, -0.5 - 0.01)
    glVertex3f(-window_size, window_size, -0.5 - 0.01)
    glEnd()

    # Left wing (hexagonal panel)
    glBegin(GL_QUADS)
    glColor3f(0.3, 0.3, 0.3)  # Dark gray for the wings
    wing_width = 0.2
    wing_height = 1.5
    wing_offset = 0.5 + wing_width / 2  # Offset from the cockpit
    vertices = [
        (-wing_offset - wing_width, -wing_height, 0), (-wing_offset + wing_width, -wing_height, 0), (-wing_offset + wing_width, wing_height, 0), (-wing_offset - wing_width, wing_height, 0),
        (-wing_offset - wing_width, -wing_height, 0.1), (-wing_offset + wing_width, -wing_height, 0.1), (-wing_offset + wing_width, wing_height, 0.1), (-wing_offset - wing_width, wing_height, 0.1),
        (-wing_offset - wing_width, -wing_height, 0), (-wing_offset - wing_width, wing_height, 0), (-wing_offset - wing_width, wing_height, 0.1), (-wing_offset - wing_width, -wing_height, 0.1),
        (-wing_offset + wing_width, -wing_height, 0), (-wing_offset + wing_width, wing_height, 0), (-wing_offset + wing_width, wing_height, 0.1), (-wing_offset + wing_width, -wing_height, 0.1),
        (-wing_offset - wing_width, wing_height, 0), (-wing_offset + wing_width, wing_height, 0), (-wing_offset + wing_width, wing_height, 0.1), (-wing_offset - wing_width, wing_height, 0.1),
        (-wing_offset - wing_width, -wing_height, 0), (-wing_offset + wing_width, -wing_height, 0), (-wing_offset + wing_width, -wing_height, 0.1), (-wing_offset - wing_width, -wing_height, 0.1)
    ]
    for i in range(0, len(vertices), 4):
        for vertex in vertices[i:i+4]:
            glVertex3fv(vertex)
    glEnd()

    # Right wing (hexagonal panel)
    glBegin(GL_QUADS)
    glColor3f(0.3, 0.3, 0.3)  # Dark gray for the wings
    vertices = [
        (wing_offset - wing_width, -wing_height, 0), (wing_offset + wing_width, -wing_height, 0), (wing_offset + wing_width, wing_height, 0), (wing_offset - wing_width, wing_height, 0),
        (wing_offset - wing_width, -wing_height, 0.1), (wing_offset + wing_width, -wing_height, 0.1), (wing_offset + wing_width, wing_height, 0.1), (wing_offset - wing_width, wing_height, 0.1),
        (wing_offset - wing_width, -wing_height, 0), (wing_offset - wing_width, wing_height, 0), (wing_offset - wing_width, wing_height, 0.1), (wing_offset - wing_width, -wing_height, 0.1),
        (wing_offset + wing_width, -wing_height, 0), (wing_offset + wing_width, wing_height, 0), (wing_offset + wing_width, wing_height, 0.1), (wing_offset + wing_width, -wing_height, 0.1),
        (wing_offset - wing_width, wing_height, 0), (wing_offset + wing_width, wing_height, 0), (wing_offset + wing_width, wing_height, 0.1), (wing_offset - wing_width, wing_height, 0.1),
        (wing_offset - wing_width, -wing_height, 0), (wing_offset + wing_width, -wing_height, 0), (wing_offset + wing_width, -wing_height, 0.1), (wing_offset - wing_width, -wing_height, 0.1)
    ]
    for i in range(0, len(vertices), 4):
        for vertex in vertices[i:i+4]:
            glVertex3fv(vertex)
    glEnd()

    glPopMatrix()

# Draw a bullet (player bullets as red cubes)
def draw_bullet(pos):
    draw_cube(pos, size=0.1, color=(1, 0, 0))

# Draw an enemy bullet (green laser line)
def draw_enemy_bullet(pos, prev_pos):
    glPushMatrix()
    glBegin(GL_LINES)
    glColor3f(0, 1, 0)  # Green for enemy laser
    glVertex3f(prev_pos[0], prev_pos[1], prev_pos[2])  # Start of the laser
    glVertex3f(pos[0], pos[1], pos[2])  # End of the laser
    glEnd()
    glPopMatrix()

# Draw a power-up (yellow cube for health)
def draw_power_up(pos):
    draw_cube(pos, size=0.3, color=(1, 1, 0))  # Yellow cube for health power-up

# Draw an explosion (simple particle effect)
def draw_explosion(explosion):
    for particle in explosion['particles']:
        draw_cube(particle['pos'], size=particle['size'], color=(1, 0.5, 0))  # Orange particles

# Draw a small hill (pyramid shape)
def draw_hill(pos, size=1.0):
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glBegin(GL_TRIANGLES)
    glColor3f(0, 0.4, 0)  # Slightly darker green for hills
    # Base
    glVertex3f(-size, 0, -size)
    glVertex3f(size, 0, -size)
    glVertex3f(size, 0, size)

    glVertex3f(-size, 0, -size)
    glVertex3f(size, 0, size)
    glVertex3f(-size, 0, size)

    # Sides
    glVertex3f(-size, 0, -size)
    glVertex3f(size, 0, -size)
    glVertex3f(0, size, 0)  # Peak

    glVertex3f(size, 0, -size)
    glVertex3f(size, 0, size)
    glVertex3f(0, size, 0)

    glVertex3f(size, 0, size)
    glVertex3f(-size, 0, size)
    glVertex3f(0, size, 0)

    glVertex3f(-size, 0, size)
    glVertex3f(-size, 0, -size)
    glVertex3f(0, size, 0)
    glEnd()
    glPopMatrix()

# Draw a tree (cone for foliage, cube for trunk)
def draw_tree(pos):
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])

    # Trunk (brown cube)
    glBegin(GL_QUADS)
    glColor3f(0.5, 0.3, 0)  # Brown
    trunk_size = 0.2
    trunk_height = 0.5
    vertices = [
        (-trunk_size, 0, -trunk_size), (-trunk_size, trunk_height, -trunk_size), (trunk_size, trunk_height, -trunk_size), (trunk_size, 0, -trunk_size),
        (-trunk_size, 0, trunk_size), (-trunk_size, trunk_height, trunk_size), (trunk_size, trunk_height, trunk_size), (trunk_size, 0, trunk_size),
        (-trunk_size, 0, -trunk_size), (-trunk_size, trunk_height, -trunk_size), (-trunk_size, trunk_height, trunk_size), (-trunk_size, 0, trunk_size),
        (trunk_size, 0, -trunk_size), (trunk_size, trunk_height, -trunk_size), (trunk_size, trunk_height, trunk_size), (trunk_size, 0, trunk_size),
        (-trunk_size, trunk_height, -trunk_size), (-trunk_size, trunk_height, trunk_size), (trunk_size, trunk_height, trunk_size), (trunk_size, trunk_height, -trunk_size),
        (-trunk_size, 0, -trunk_size), (-trunk_size, 0, trunk_size), (trunk_size, 0, trunk_size), (trunk_size, 0, -trunk_size)
    ]
    for i in range(0, len(vertices), 4):
        for vertex in vertices[i:i+4]:
            glVertex3fv(vertex)
    glEnd()

    # Foliage (green cone)
    glBegin(GL_TRIANGLES)
    glColor3f(0, 0.6, 0)  # Green
    foliage_base = 0.5
    foliage_height = 1.0
    glVertex3f(-foliage_base, trunk_height, -foliage_base)
    glVertex3f(foliage_base, trunk_height, -foliage_base)
    glVertex3f(0, trunk_height + foliage_height, 0)

    glVertex3f(foliage_base, trunk_height, -foliage_base)
    glVertex3f(foliage_base, trunk_height, foliage_base)
    glVertex3f(0, trunk_height + foliage_height, 0)

    glVertex3f(foliage_base, trunk_height, foliage_base)
    glVertex3f(-foliage_base, trunk_height, foliage_base)
    glVertex3f(0, trunk_height + foliage_height, 0)

    glVertex3f(-foliage_base, trunk_height, foliage_base)
    glVertex3f(-foliage_base, trunk_height, -foliage_base)
    glVertex3f(0, trunk_height + foliage_height, 0)
    glEnd()

    glPopMatrix()

# Draw a terrain segment
def draw_terrain_segment(z_offset, base_z):
    glPushMatrix()
    glTranslatef(0, 0, z_offset)
    glBegin(GL_QUADS)
    glColor3f(0, 0.5, 0)
    glVertex3f(-10, -2, -10)
    glVertex3f(10, -2, -10)
    glVertex3f(10, -2, 10)
    glVertex3f(-10, -2, 10)
    glEnd()

    for feature in terrain_features[base_z]:
        if feature['type'] == 'hill':
            draw_hill([feature['x'], -2, feature['z']], size=feature['size'])
        elif feature['type'] == 'tree':
            draw_tree([feature['x'], -2, feature['z']])

    glPopMatrix()

# Generate random terrain features
def generate_terrain_features(z_offset):
    features = []
    for _ in range(random.randint(3, 5)):
        x = random.uniform(-8, 8)
        z = random.uniform(-8, 8)
        size = random.uniform(0.5, 1.5)
        features.append({'type': 'hill', 'x': x, 'z': z, 'size': size})

    for _ in range(random.randint(5, 10)):
        x = random.uniform(-8, 8)
        z = random.uniform(-8, 8)
        features.append({'type': 'tree', 'x': x, 'z': z})

    return features

# Draw a simple skybox (gradient sky)
def draw_skybox():
    glPushMatrix()
    glDisable(GL_DEPTH_TEST)  # Disable depth test for skybox
    glBegin(GL_QUADS)
    # Skybox (gradient from light blue at the top to darker blue at the bottom)
    glColor3f(0.2, 0.4, 0.8)  # Light blue at the top
    glVertex3f(-50, 50, -50)
    glVertex3f(50, 50, -50)
    glColor3f(0.1, 0.2, 0.4)  # Darker blue at the bottom
    glVertex3f(50, -50, -50)
    glVertex3f(-50, -50, -50)

    glColor3f(0.2, 0.4, 0.8)
    glVertex3f(-50, 50, 50)
    glVertex3f(50, 50, 50)
    glColor3f(0.1, 0.2, 0.4)
    glVertex3f(50, -50, 50)
    glVertex3f(-50, -50, 50)

    glColor3f(0.2, 0.4, 0.8)
    glVertex3f(-50, 50, -50)
    glVertex3f(-50, 50, 50)
    glColor3f(0.1, 0.2, 0.4)
    glVertex3f(-50, -50, 50)
    glVertex3f(-50, -50, -50)

    glColor3f(0.2, 0.4, 0.8)
    glVertex3f(50, 50, -50)
    glVertex3f(50, 50, 50)
    glColor3f(0.1, 0.2, 0.4)
    glVertex3f(50, -50, 50)
    glVertex3f(50, -50, -50)

    glColor3f(0.2, 0.4, 0.8)
    glVertex3f(-50, 50, -50)
    glVertex3f(50, 50, -50)
    glVertex3f(50, 50, 50)
    glVertex3f(-50, 50, 50)
    glEnd()
    glEnable(GL_DEPTH_TEST)  # Re-enable depth test
    glPopMatrix()

# Draw text (simplified version using a pre-rendered texture)
def draw_text(text, x, y, color=(255, 0, 0)):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, display[0], 0, display[1], -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Pre-render the text as a texture
    pygame.font.init()
    font = pygame.font.Font(None, 74)
    text_surface = font.render(text, True, color)
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    text_width, text_height = text_surface.get_size()

    # Draw the texture
    glRasterPos2f(x, y)
    glDrawPixels(text_width, text_height, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# Reset the game state
def reset_game():
    global player_pos, player_rotation, player_velocity, player_health, enemies, bullets, enemy_bullets, explosions, power_ups, game_over, game_active, score
    player_pos = [0, 0, 0]
    player_rotation = [0, 0, 0]
    player_velocity = [0, 0, 0]
    player_health = 3  # Reset health
    enemies = []
    bullets = []
    enemy_bullets = []
    explosions = []
    power_ups = []
    score = 0  # Reset score
    game_over = False
    game_active = True
    # Restart background music
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
    pygame.mixer.music.play(-1)

# Main game loop
def main():
    global player_pos, player_rotation, player_velocity, player_health, enemies, bullets, enemy_bullets, explosions, power_ups, game_over, game_active, terrain_segments, terrain_features, score
    
    for segment in terrain_segments:
        terrain_features[segment['base_z']] = generate_terrain_features(segment['base_z'])

    clock = pygame.time.Clock()
    enemy_spawn_timer = 0
    enemy_shoot_timer = 0
    power_up_spawn_timer = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_active:
                    bullets.append([player_pos[0], player_pos[1], player_pos[2]])
                    # Play shooting sound
                    if shoot_sound:
                        print("Playing shoot sound")
                        shoot_sound.play()
                if game_over:  # Restart on any key press when game is over
                    reset_game()

        if not game_active:
            if game_over:
                draw_text("Game Over", display[0] // 2 - 100, display[1] // 2)
            pygame.display.flip()
            clock.tick(60)
            continue

        # Player movement
        keys = pygame.key.get_pressed()
        target_velocity = [0, 0, 0]
        rotation_speed = 2.0

        if keys[pygame.K_LEFT]:
            target_velocity[0] = -0.1
            player_rotation[2] = min(player_rotation[2] + rotation_speed, 30)
        elif keys[pygame.K_RIGHT]:
            target_velocity[0] = 0.1
            player_rotation[2] = max(player_rotation[2] - rotation_speed, -30)
        else:
            player_rotation[2] *= 0.9

        if keys[pygame.K_UP]:
            target_velocity[1] = 0.1
            player_rotation[0] = max(player_rotation[0] - rotation_speed, -30)
        elif keys[pygame.K_DOWN]:
            target_velocity[1] = -0.1
            player_rotation[0] = min(player_rotation[0] + rotation_speed, 30)
        else:
            player_rotation[0] *= 0.9

        if keys[pygame.K_q]:
            player_rotation[1] += rotation_speed
        if keys[pygame.K_e]:
            player_rotation[1] -= rotation_speed

        for i in range(3):
            player_velocity[i] = player_velocity[i] * 0.9 + target_velocity[i] * 0.1
            player_pos[i] += player_velocity[i]

        # Spawn enemies from the front (negative z-direction)
        enemy_spawn_timer += 1
        if enemy_spawn_timer > 60:  # Spawn every 60 frames (1 second at 60 FPS)
            x = random.uniform(-5, 5)
            y = random.uniform(-2, 2)
            enemies.append([x, y, -30])  # Spawn at z=-30 (in front of player)
            enemy_spawn_timer = 0

        # Spawn power-ups occasionally
        power_up_spawn_timer += 1
        if power_up_spawn_timer > 300:  # Spawn every 300 frames (5 seconds at 60 FPS)
            x = random.uniform(-5, 5)
            y = random.uniform(-2, 2)
            power_ups.append({'pos': [x, y, -30], 'prev_pos': [x, y, -30]})  # Spawn at z=-30
            power_up_spawn_timer = 0

        # Update enemies (move toward player)
        for enemy in enemies[:]:
            enemy[2] += terrain_speed  # Move toward player (increase z toward z=0)
            # Also apply some AI movement toward the player in x and y
            enemy[0] += (player_pos[0] - enemy[0]) * enemy_speed
            enemy[1] += (player_pos[1] - enemy[1]) * enemy_speed
            if enemy[2] > 10:  # Remove if too far behind
                enemies.remove(enemy)
            # Check collision with player
            if (abs(enemy[0] - player_pos[0]) < 1.0 and
                abs(enemy[1] - player_pos[1]) < 1.0 and
                abs(enemy[2] - player_pos[2]) < 1.0):
                player_health -= 1
                enemies.remove(enemy)
                if player_health <= 0:
                    game_over = True
                    game_active = False

        # Enemies shoot at the player
        enemy_shoot_timer += 1
        if enemy_shoot_timer > 120:  # Shoot every 2 seconds
            for enemy in enemies:
                enemy_bullets.append({'pos': [enemy[0], enemy[1], enemy[2]], 'prev_pos': [enemy[0], enemy[1], enemy[2]]})
            enemy_shoot_timer = 0

        # Update enemy bullets
        for bullet in enemy_bullets[:]:
            bullet['prev_pos'] = bullet['pos'].copy()  # Store previous position for drawing
            bullet['pos'][2] += 0.2  # Move toward player (increase z toward z=0)
            if bullet['pos'][2] > 20:
                enemy_bullets.remove(bullet)
            # Check collision with player
            if (abs(bullet['pos'][0] - player_pos[0]) < 0.5 and
                abs(bullet['pos'][1] - player_pos[1]) < 0.5 and
                abs(bullet['pos'][2] - player_pos[2]) < 0.5):
                player_health -= 1
                enemy_bullets.remove(bullet)
                if player_health <= 0:
                    game_over = True
                    game_active = False

        # Update power-ups
        for power_up in power_ups[:]:
            power_up['prev_pos'] = power_up['pos'].copy()  # Store previous position
            power_up['pos'][2] += terrain_speed  # Move toward player (increase z toward z=0)
            if power_up['pos'][2] > 10:  # Remove if too far behind
                power_ups.remove(power_up)
            # Check collision with player
            if (abs(power_up['pos'][0] - player_pos[0]) < 0.5 and
                abs(power_up['pos'][1] - player_pos[1]) < 0.5 and
                abs(power_up['pos'][2] - player_pos[2]) < 0.5):
                player_health = min(player_health + 1, 5)  # Increase health, max 5
                power_ups.remove(power_up)

        # Update terrain
        for segment in terrain_segments:
            segment['current_z'] += terrain_speed
            if segment['current_z'] > 20:
                segment['current_z'] -= 60
                segment['base_z'] -= 60
                terrain_features[segment['base_z']] = generate_terrain_features(segment['base_z'])

        # Update bullets (collect bullets to remove to avoid double-removal)
        bullets_to_remove = []
        for bullet in bullets:
            bullet[2] -= 0.2  # Move forward (decrease z)
            if bullet[2] < -20:
                bullets_to_remove.append(bullet)
                continue  # Skip further checks for this bullet
            # Check collision with enemies
            for enemy in enemies[:]:
                if (abs(bullet[0] - enemy[0]) < 1.0 and
                    abs(bullet[1] - enemy[1]) < 1.0 and
                    abs(bullet[2] - enemy[2]) < 1.0):
                    # Create explosion
                    particles = []
                    for _ in range(10):
                        particles.append({
                            'pos': [enemy[0], enemy[1], enemy[2]],
                            'vel': [random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1)],
                            'size': 0.2,
                            'lifetime': 30
                        })
                    explosions.append({'particles': particles})
                    # Play explosion sound
                    if explosion_sound:
                        print("Playing explosion sound")
                        explosion_sound.play()
                    enemies.remove(enemy)
                    bullets_to_remove.append(bullet)
                    score += 100  # Increase score by 100 points for destroying an enemy
                    break

        # Remove bullets after the loop
        for bullet in bullets_to_remove:
            if bullet in bullets:  # Ensure bullet is still in the list
                bullets.remove(bullet)

        # Update explosions
        for explosion in explosions[:]:
            for particle in explosion['particles']:
                particle['pos'][0] += particle['vel'][0]
                particle['pos'][1] += particle['vel'][1]
                particle['pos'][2] += particle['vel'][2]
                particle['lifetime'] -= 1
                particle['size'] *= 0.95
            explosion['particles'] = [p for p in explosion['particles'] if p['lifetime'] > 0]
            if not explosion['particles']:
                explosions.remove(explosion)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        # Draw skybox
        draw_skybox()

        # Draw terrain
        for segment in terrain_segments:
            draw_terrain_segment(segment['current_z'], segment['base_z'])

        # Draw game elements
        draw_arwing(player_pos, player_rotation, scale=0.5)
        for enemy in enemies:
            if enemy_model:
                draw_model(enemy_model, enemy, scale=1.0, color=(1, 0, 0))
            else:
                draw_tie_fighter(enemy, scale=1.0)  # Use TIE Fighter design
        for bullet in bullets:
            draw_bullet(bullet)
        for bullet in enemy_bullets:
            draw_enemy_bullet(bullet['pos'], bullet['prev_pos'])
        for power_up in power_ups:
            draw_power_up(power_up['pos'])

        # Draw HUD (health and score)
        draw_text(f"Health: {player_health}", 10, display[1] - 40, color=(0, 255, 0))  # Green text for health
        draw_text(f"Score: {score} pts", 10, display[1] - 80, color=(255, 255, 0))  # Yellow text for score with "pts"

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
