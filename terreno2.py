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
poly_data = {'pos': [0, 0, 4.5]}
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

# Funciones de utilidades
def offset_polygon(polygon, offset):
    return [[p[0] + offset[0], p[1] + offset[1], p[2] + offset[2]] for p in polygon]

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

    # Generar y mover las nubes
    generate_clouds()
    move_clouds()

    # Dibujar las nubes
    draw_clouds()

    # Procesar eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Click izquierdo
                mouse_dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Liberar click izquierdo
                mouse_dragging = False
        elif event.type == pygame.MOUSEMOTION and mouse_dragging:
            dx, dy = event.rel
            poly_data['pos'][0] += dx * mouse_sensitivity
            poly_data['pos'][1] -= dy * mouse_sensitivity

    # Actualizar terreno si es necesario
    if polygons[-1][0][0][2] < -poly_data['pos'][2]:
        polygons = polygons[:-30]
        generate_poly_row(len(polygons) // 50 + 26)

    # Renderizar polígonos
    for polygon, color in polygons:
        pygame.draw.polygon(screen, color, project_polygon(offset_polygon(polygon, poly_data['pos'])))

    pygame.display.flip()
    clock.tick(60)
