# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_python_blender_code_that_creates_a_model_of_wall_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write python blender code that creates a model of wall pattern

import bpy

# Step 1: Clear Existing Objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define parameters for the hexagonal grid
hex_size = 1.0
height_of_hex = 0.1
hex_spacing = 1.5

# Function to generate a hexagon at a given position
def generate_hexagon(position):
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=hex_size, depth=height_of_hex, location=position)
    return bpy.context.object

# Step 2: Create a grid of hexagons
num_rows = 5
num_cols = 5

for r in range(num_rows):
    for c in range(num_cols):
        x_coord = c * hex_size * 2
        y_coord = r * hex_size * 2
        generate_hexagon((x_coord, y_coord, 0))

# Final adjustments to ensure uniformity
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.transform.resize(value=(1, 1, 1))
bpy.ops.object.select_all(action='DESELECT')
