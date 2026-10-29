# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_python_code_that_makes_a_model_of_sphere_and_move_it_upward_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender python code that makes a model of sphere and move it upward by 3 units

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))

# Move the sphere upward by 3 units
bpy.ops.transform.translate(value=(0, 0, 3))
