# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_for_generating_a_model_of_spiral_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code for generating a model of spiral pattern.

import bpy
import math

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Generate a spiral using a functional approach

def spiral_spheres(turns, points_per_turn, sphere_radius, height_increment):
    for i in range(turns * points_per_turn):
        angle = i * (2 * math.pi / points_per_turn)
        x = sphere_radius * angle * math.cos(angle)
        y = sphere_radius * angle * math.sin(angle)
        z = height_increment * (i / points_per_turn)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(x, y, z))

# Parameters for the spiral
num_turns = 5
points_per_turn = 50
spiral_radius = 0.1
height_per_point = 0.1

# Create the spiral
spiral_spheres(num_turns, points_per_turn, spiral_radius, height_per_point)
