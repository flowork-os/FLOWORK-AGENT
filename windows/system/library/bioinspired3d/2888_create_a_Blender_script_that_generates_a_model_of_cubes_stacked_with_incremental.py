# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_Blender_script_that_generates_a_model_of_cubes_stacked_with_incremental" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a Blender script that generates a model of cubes stacked with incremental rotation to form a spiral.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the spiral
num_cubes = 50  # Number of cubes
distance = 0.5  # Distance between cubes
angle_increment = 10  # Degrees to rotate each cube

for i in range(num_cubes):
    # Create a cube
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, i * distance))
    cube = bpy.context.object
    
    # Rotate the cube
    rotation_angle = math.radians(i * angle_increment)
    cube.rotation_euler[2] = rotation_angle  # Rotate around Z-axis
