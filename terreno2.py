import pygame
import sys
import math
from copy import deepcopy
from pyswip import Prolog
import noise
import random

# Inicialización
pygame.init()
pygame.display.set_caption('Terreno Procedural 3D')
screen = pygame.display.set_mode((500, 500))
clock = pygame.time.Clock()
FOV, WIDTH, HEIGHT = 90, *screen.get_size()

# Inicialización de Prolog
prolog = Prolog()
prolog.consult("generador.pl")

# Configuración de terreno
poly_data = {'pos': [0, 0, 4.5], 'rotation': [0, 0]}  # Posición y rotación de la cámara
square_polygon = [[-0.5, 0.5, -0.5], [0.5, 0.5, -0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, 0.5]]
polygons, altura_cache, color_cache = [], {}, {}

# Movimiento del mouse
mouse_dragging = False
mouse_sensitivity = 0.1

# Nubes
clouds = []
def generate_clouds():
    global clouds
    if len(clouds) < 5:  # Limitar el número de nubes en la pantalla
        x_pos = random.randint(0, WIDTH)
        y_pos = random.randint(20, 100)  # Las nubes estarán en la parte superior
        cloud_size = random.randint(30, 100)
        clouds.append([x_pos, y_pos, cloud_size])

def move_clouds():
    global clouds
    for cloud in clouds:
        cloud[0] += 0.1  # Movimiento suave de las nubes a la derecha
        if cloud[0] > WIDTH:  # Si la nube se sale de la pantalla, vuelve al inicio
            cloud[0] = -cloud[2]

def draw_clouds():
    for cloud in clouds:
        pygame.draw.circle(screen, (255, 255, 255), (int(cloud[0]), int(cloud[1])), cloud[2])

# Sol
sun_pos = [400, 100]  # Posición inicial del sol
sun_radius = 50  # Radio del sol
sun_color = (255, 255, 0)  # Color amarillo del sol

def draw_sun_rays(sun_pos, sun_radius, num_rays=12, ray_length=30, ray_color=(255, 223, 0)):
    angle_step = 360 / num_rays
    for i in range(num_rays):
        angle = math.radians(i * angle_step)
        inner_x = sun_pos[0] + sun_radius * math.cos(angle)
        inner_y = sun_pos[1] + sun_radius * math.sin(angle)
        outer_x1 = sun_pos[0] + (sun_radius + ray_length) * math.cos(angle - math.radians(5))
        outer_y1 = sun_pos[1] + (sun_radius + ray_length) * math.sin(angle - math.radians(5))
        outer_x2 = sun_pos[0] + (sun_radius + ray_length) * math.cos(angle + math.radians(5))
        outer_y2 = sun_pos[1] + (sun_radius + ray_length) * math.sin(angle + math.radians(5))
        pygame.draw.polygon(screen, ray_color, [(inner_x, inner_y), (outer_x1, outer_y1), (outer_x2, outer_y2)])

# Funciones de utilidades
def offset_polygon(polygon, offset):
    return [[p[0] + offset[0], p[1] + offset[1], p[2] + offset[2]] for p in polygon]

def rotate_point(point, angle_x, angle_y):
    """Rotar un punto alrededor del eje X e Y."""
    x, y, z = point
    # Rotación en el eje Y
    cosa, sina = math.cos(angle_y), math.sin(angle_y)
    x, z = cosa * x - sina * z, sina * x + cosa * z
    # Rotación en el eje X
    cosb, sinb = math.cos(angle_x), math.sin(angle_x)
    y, z = cosb * y - sinb * z, sinb * y + cosb * z
    return [x, y, z]

def project_polygon(polygon):
    return [[
        (math.atan2(p[0], p[2]) / math.radians(FOV)) * WIDTH + WIDTH // 2,
        (math.atan2(p[1], p[2]) / math.radians(FOV)) * HEIGHT + HEIGHT // 2
    ] for p in polygon]

def get_altura(x, y):
    if (x, y) not in altura_cache:
        perlin_value = noise.pnoise2(x / 10, y / 10)
        altura = next(iter(prolog.query(f"altura({x}, {y}, {perlin_value}, A)")), {}).get('A', 0)
        altura_cache[(x, y)] = altura
    return altura_cache[(x, y)]

def get_color(altura):
    if altura not in color_cache:
        color = next(iter(prolog.query(f"color({altura}, R, G, B)")), {'R': 255, 'G': 255, 'B': 255})
        color_cache[altura] = (color['R'], color['G'], color['B'])
    return color_cache[altura]

def generate_poly_row(y):
    for x in range(50):
        polygon = offset_polygon(square_polygon, [x - 25, 5, y + 5])
        for corner in polygon:
            corner[1] -= get_altura(corner[0], corner[2])
        altura_promedio = sum(p[1] for p in polygon) / len(polygon)
        polygons.insert(0, [polygon, get_color(altura_promedio)])

# Generar terreno inicial
for y in range(26):
    generate_poly_row(y)

# Bucle principal
while True:
    screen.fill((100, 200, 250))  # Fondo de cielo
    poly_data['pos'][2] -= 0.25

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:  # Mover hacia adelante
        poly_data['pos'][2] += 0.5
    if keys[pygame.K_s]:  # Mover hacia atrás
        poly_data['pos'][2] -= 0.5
    if keys[pygame.K_a]:  # Rotar izquierda
        poly_data['rotation'][1] += 0.05
    if keys[pygame.K_d]:  # Rotar derecha
        poly_data['rotation'][1] -= 0.05

    generate_clouds()
    move_clouds()

    # Dibujar el sol
    pygame.draw.circle(screen, sun_color, sun_pos, sun_radius)
    draw_sun_rays(sun_pos, sun_radius)

    draw_clouds()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Actualizar terreno si es necesario
    if polygons[-1][0][0][2] < -poly_data['pos'][2]:
        polygons = polygons[:-30]
        generate_poly_row(len(polygons) // 50 + 26)

    # Renderizar polígonos
    for polygon, color in polygons:
        rotated = [rotate_point(corner, poly_data['rotation'][0], poly_data['rotation'][1]) for corner in polygon]
        projected = project_polygon(offset_polygon(rotated, poly_data['pos']))
        pygame.draw.polygon(screen, color, projected)

    pygame.display.flip()
    clock.tick(60)

