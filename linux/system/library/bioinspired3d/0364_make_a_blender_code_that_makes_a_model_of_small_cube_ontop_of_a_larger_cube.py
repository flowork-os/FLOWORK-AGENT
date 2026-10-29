# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_blender_code_that_makes_a_model_of_small_cube_ontop_of_a_larger_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a blender code that makes a model of small cube ontop of a larger cube

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a larger cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))

# Create a smaller cube on top of the larger cube
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 2.5))
