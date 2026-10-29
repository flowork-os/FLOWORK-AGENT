# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_code_make_geometric_wall_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender code make geometric wall pattern.

import bpy
import math

# Clear the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Class to manage shape creation
class ShapeCreator:
    @staticmethod
    def add_hexagon(radius, location):
        bpy.ops.mesh.primitive_circle_add(vertices=6, radius=radius, fill_type='NGON', location=location)
        hexagon = bpy.context.object
        hexagon.name = f"Hexagon_{radius}_{location}"

    @staticmethod
    def add_triangle(radius, location):
        bpy.ops.mesh.primitive_circle_add(vertices=3, radius=radius, fill_type='NGON', location=location)
        triangle = bpy.context.object
        triangle.name = f"Triangle_{radius}_{location}"

# Define sizes for the shapes
shape_sizes = [1, 0.75, 0.5]
# Define hexagon positions
hexagon_positions = [(0, 0, 0), (2, 0, 0), (1, math.sqrt(3), 0), (-1, math.sqrt(3), 0), (-2, 0, 0), (-1, -math.sqrt(3), 0), (1, -math.sqrt(3), 0)]
# Define triangle positions
triangle_positions = [(1, 0, 0), (1.5, math.sqrt(3)/2, 0), (0.5, math.sqrt(3)/2, 0), (-0.5, math.sqrt(3)/2, 0), (-1.5, math.sqrt(3)/2, 0), (-1, 0, 0), (-0.5, -math.sqrt(3)/2, 0), (0.5, -math.sqrt(3)/2, 0), (1.5, -math.sqrt(3)/2, 0)]

# Generate hexagons
for size in shape_sizes:
    for position in hexagon_positions:
        ShapeCreator.add_hexagon(size, (position[0] * size * 2, position[1] * size * 2, 0))

# Generate triangles
for size in shape_sizes:
    for position in triangle_positions:
        ShapeCreator.add_triangle(size, (position[0] * size * 2, position[1] * size * 2, 0))
