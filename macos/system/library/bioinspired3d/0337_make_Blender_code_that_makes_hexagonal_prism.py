# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_Blender_code_that_makes_hexagonal_prism" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make Blender code that makes hexagonal prism.

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a hexagonal prism
bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=1, depth=2, location=(0, 0, 0))
