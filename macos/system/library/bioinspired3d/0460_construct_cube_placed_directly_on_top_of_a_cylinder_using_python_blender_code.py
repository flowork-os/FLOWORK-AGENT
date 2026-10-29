# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_cube_placed_directly_on_top_of_a_cylinder_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct cube placed directly on top of a cylinder using python blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 1))
cylinder = bpy.context.object

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 3))
cube = bpy.context.object
