import pygame
import sys
import math
from copy import deepcopy
from pyswip import Prolog
import noise

# Inicialización de Pygame
pygame.init()
pygame.display.set_caption('Terreno procedural 3D con Prolog | Proyecto de Investigación | UTP')
screen = pygame.display.set_mode((500, 500))
clock = pygame.time.Clock()

FOV = 90

def offset_polygon(polygon, offset):
    for point in polygon:
        point[0] += offset[0]
        point[1] += offset[1]
        point[2] += offset[2]

def project_polygon(polygon):
    projected_points = []
    for point in polygon:
        x_angle = math.atan2(point[0], point[2])
        y_angle = math.atan2(point[1], point[2])
        x = x_angle / math.radians(FOV) * screen.get_width() + screen.get_height() // 2
        y = y_angle / math.radians(FOV) * screen.get_width() + screen.get_width() // 2
        projected_points.append([x, y])
    return projected_points

def gen_polygon(polygon_base, polygon_data):
    generated_polygon = deepcopy(polygon_base)
    offset_polygon(generated_polygon, polygon_data['pos'])
    return project_polygon(generated_polygon)

# Configuración del terreno
poly_data = {
    'pos': [0, 0, 4.5],
    'rot': [0, 0, 0],
}

square_polygon = [
    [-0.5, 0.5, -0.5],
    [0.5, 0.5, -0.5],
    [0.5, 0.5, 0.5],
    [-0.5, 0.5, 0.5],
]

polygons = []
prolog = Prolog()
prolog.consult("generador.pl")  # Consulta de parametros de prolog

def generate_poly_row(y):
    global polygons
    for x in range(50):  
        poly_copy = deepcopy(square_polygon)
        offset_polygon(poly_copy, [x - 25, 5, y + 5])  # desplazamiento

        # Consulta de altura en
        for corner in poly_copy:
            print(f"Consultando altura para ({corner[0]}, {corner[2]})")  
            altura_query = list(prolog.query(f"altura({corner[0]}, {corner[2]}, Altura)"))
            if not altura_query:
                print(f"No se encontró altura para ({corner[0]}, {corner[2]})")
                altura = 0  
            else:
                altura = altura_query[0]['Altura']
            corner[1] -= altura

        # Consulta del color basado en Prolog
        altura_promedio = sum([corner[1] for corner in poly_copy]) / len(poly_copy)
        color_query = list(prolog.query(f"color({altura_promedio}, R, G, B)"))
        if not color_query:
            print(f"No se encontró color para altura promedio {altura_promedio}")
            color = (255, 255, 255)  
        else:
            color = tuple(color_query[0][channel] for channel in ['R', 'G', 'B'])

        polygons = [[poly_copy, color]] + polygons

# Generar filas 
next_row = 0
for y in range(26):
    generate_poly_row(y)
    next_row += 1

# Loop 
while True:
    screen.fill((100, 200, 250))
    poly_data['pos'][2] -= 0.25

    if polygons[-1][0][0][2] < -poly_data['pos'][2]:
        for _ in range(30):
            polygons.pop(len(polygons) - 1)
        generate_poly_row(next_row)
        next_row += 1

    for polygon in polygons:
        render_poly = gen_polygon(polygon[0], poly_data)
        pygame.draw.polygon(screen, polygon[1], render_poly)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    pygame.display.flip()
    clock.tick(60)