# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_that_makes_a_model_of_wall_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code that makes a model of wall pattern.

import bpy

# Step 1: Clear the current mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Hexagon configuration
hexagon_radius = 1.0
hexagon_depth = 0.1
hexagon_gap = 1.5

# Function to create hexagons in a grid
def create_hexagon_grid(rows, cols):
    for row in range(rows):
        for col in range(cols):
            x_position = col * hexagon_radius * 2
            y_position = row * hexagon_radius * 2
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=hexagon_radius, depth=hexagon_depth, location=(x_position, y_position, 0))

# Step 2: Generate a grid of hexagons
create_hexagon_grid(5, 5)

# Step 3: Select all hexagons for final adjustments
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.transform.resize(value=(1, 1, 1))
bpy.ops.object.select_all(action='DESELECT')
