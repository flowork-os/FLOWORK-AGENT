# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_generates_cubes_stacked_with_incremental_rotation_to_form" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that generates cubes stacked with incremental rotation to form a spiral.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_cubes = 50  # Number of cubes
height_increment = 0.2  # Height increment for each cube
angle_increment = 10  # Angle increment in degrees

for i in range(num_cubes):
    # Create a cube
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, i * height_increment))
    cube = bpy.context.object
    
    # Calculate rotation
    angle = math.radians(i * angle_increment)
    cube.rotation_euler = (0, 0, angle)
    
    # Move the cube along the X and Y axes to form a spiral
    radius = i * 0.1  # Radius increment for the spiral
    cube.location.x = radius * math.cos(angle)
    cube.location.y = radius * math.sin(angle)
