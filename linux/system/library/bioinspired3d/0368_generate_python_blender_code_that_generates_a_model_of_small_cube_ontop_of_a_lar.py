# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_python_blender_code_that_generates_a_model_of_small_cube_ontop_of_a_lar" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate python blender code that generates a model of small cube ontop of a larger cube.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a larger cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))  # Larger cube at Z=1

# Create a smaller cube
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 2.5))  # Smaller cube on top of larger cube
