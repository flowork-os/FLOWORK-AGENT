# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_cubes_stacked_with_incremental_rotation_to_form_a_spiral_using_p" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of cubes stacked with incremental rotation to form a spiral using python blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters
num_cubes = 20
cube_size = 0.5
angle_increment = math.radians(15)  # 15 degrees in radians
height_increment = 0.5

# Create cubes in a spiral
for i in range(num_cubes):
    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, i * height_increment))
    cube = bpy.context.object
    # Rotate the cube
    cube.rotation_euler[2] = i * angle_increment  # Rotate around Z-axis
    # Move the cube outward in a circular pattern
    radius = i * 0.1  # Incremental radius
    cube.location.x += radius * math.cos(i * angle_increment)
    cube.location.y += radius * math.sin(i * angle_increment)
