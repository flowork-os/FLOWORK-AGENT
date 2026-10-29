# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_code_that_creates_a_model_of_geometric_wall_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender code that creates a model of geometric wall pattern.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_polygon(sides, radius, position):
    bpy.ops.mesh.primitive_circle_add(vertices=sides, radius=radius, fill_type='NGON', location=position)
    polygon = bpy.context.object
    polygon.name = f"Polygon_{sides}_{radius}_{position}"

shape_dimensions = [1, 0.75, 0.5]
hexagon_coords = [
    (0, 0, 0), 
    (2, 0, 0), 
    (1, math.sqrt(3), 0), 
    (-1, math.sqrt(3), 0), 
    (-2, 0, 0), 
    (-1, -math.sqrt(3), 0), 
    (1, -math.sqrt(3), 0)
]
triangle_coords = [
    (1, 0, 0), 
    (1.5, math.sqrt(3)/2, 0), 
    (0.5, math.sqrt(3)/2, 0), 
    (-0.5, math.sqrt(3)/2, 0), 
    (-1.5, math.sqrt(3)/2, 0), 
    (-1, 0, 0), 
    (-0.5, -math.sqrt(3)/2, 0), 
    (0.5, -math.sqrt(3)/2, 0), 
    (1.5, -math.sqrt(3)/2, 0)
]

for size in shape_dimensions:
    for coord in hexagon_coords:
        create_polygon(6, size, (coord[0] * size * 2, coord[1] * size * 2, 0))

for size in shape_dimensions:
    for coord in triangle_coords:
        create_polygon(3, size, (coord[0] * size * 2, coord[1] * size * 2, 0))
