# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_cubes_stacked_with_incremental_rotation_to_form_a_spiral_using_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate cubes stacked with incremental rotation to form a spiral using Blender Python script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_cubes = 30  # Number of cubes in the spiral
distance = 0.5  # Distance between cubes
angle_increment = 15  # Degrees to rotate each cube

for i in range(num_cubes):
    # Create a cube
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, i * distance))
    cube = bpy.context.object
    
    # Rotate the cube
    rotation_angle = math.radians(i * angle_increment)
    cube.rotation_euler = (0, 0, rotation_angle)
