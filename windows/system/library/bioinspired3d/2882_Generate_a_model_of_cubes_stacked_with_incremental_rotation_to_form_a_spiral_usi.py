# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_cubes_stacked_with_incremental_rotation_to_form_a_spiral_usi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of cubes stacked with incremental rotation to form a spiral using code in Blender

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters
num_cubes = 30  # Number of cubes in the spiral
cube_size = 0.5  # Size of each cube
height_increment = 0.5  # Height increment for each cube
rotation_increment = 15  # Rotation increment in degrees

# Create cubes in a spiral
for i in range(num_cubes):
    # Create a cube
    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, i * height_increment))
    cube = bpy.context.object
    
    # Rotate the cube
    rotation_angle = math.radians(i * rotation_increment)
    cube.rotation_euler[2] = rotation_angle  # Rotate around Z-axis
