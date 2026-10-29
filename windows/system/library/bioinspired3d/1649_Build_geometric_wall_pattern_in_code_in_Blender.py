# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_geometric_wall_pattern_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build geometric wall pattern in code in Blender

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to generate a hexagonal shape
def generate_hexagon(radius, position):
    bpy.ops.mesh.primitive_circle_add(vertices=6, radius=radius, fill_type='NGON', location=position)
    hexagon_object = bpy.context.object
    hexagon_object.name = f"Hexagon_{radius}_{position}"

# Function to generate a triangular shape
def generate_triangle(radius, position):
    bpy.ops.mesh.primitive_circle_add(vertices=3, radius=radius, fill_type='NGON', location=position)
    triangle_object = bpy.context.object
    triangle_object.name = f"Triangle_{radius}_{position}"

# Define sizes for the shapes
shape_sizes = [1, 0.75, 0.5]
# Define positions for hexagons
hexagon_coords = [
    (0, 0, 0), 
    (2, 0, 0), 
    (1, math.sqrt(3), 0), 
    (-1, math.sqrt(3), 0), 
    (-2, 0, 0), 
    (-1, -math.sqrt(3), 0), 
    (1, -math.sqrt(3), 0)
]
# Define positions for triangles
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

# Create hexagons in the scene
for size in shape_sizes:
    for coord in hexagon_coords:
        generate_hexagon(size, (coord[0] * size * 2, coord[1] * size * 2, 0))

# Create triangles in the scene
for size in shape_sizes:
    for coord in triangle_coords:
        generate_triangle(size, (coord[0] * size * 2, coord[1] * size * 2, 0))
