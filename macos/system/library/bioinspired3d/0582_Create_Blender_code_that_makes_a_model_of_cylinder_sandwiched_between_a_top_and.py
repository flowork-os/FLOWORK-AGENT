# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_Blender_code_that_makes_a_model_of_cylinder_sandwiched_between_a_top_and" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create Blender code that makes a model of cylinder sandwiched between a top and bottom rectangular prism.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))

# Create the top rectangular prism
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1.5))
bpy.ops.transform.resize(value=(1, 1, 0.5))

# Create the bottom rectangular prism
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, -1.5))
bpy.ops.transform.resize(value=(1, 1, 0.5))
