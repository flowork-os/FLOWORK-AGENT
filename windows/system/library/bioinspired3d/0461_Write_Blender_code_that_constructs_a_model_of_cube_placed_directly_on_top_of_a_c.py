# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_code_that_constructs_a_model_of_cube_placed_directly_on_top_of_a_c" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender code that constructs a model of cube placed directly on top of a cylinder

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 1))

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 3))
