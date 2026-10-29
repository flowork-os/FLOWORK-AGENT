# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_Blender_script_that_makes_cubes_stacked_with_incremental_rotation_to_form" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a Blender script that makes cubes stacked with incremental rotation to form a spiral.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_cubes = 30  # Number of cubes
height_increment = 0.5  # Height increment for each cube
angle_increment = 10  # Angle increment in degrees

for i in range(num_cubes):
    # Create a cube
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, i * height_increment))
    cube = bpy.context.object
    
    # Calculate rotation and position
    angle = math.radians(i * angle_increment)
    cube.rotation_euler[2] = angle  # Rotate around Z-axis
    cube.location.x = math.cos(angle)  # X position based on angle
    cube.location.y = math.sin(angle)  # Y position based on angle
