# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_python_blender_code_construct_hexagonal_prism" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using python blender code construct hexagonal prism.

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a hexagonal prism
bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=1, depth=2, location=(0, 0, 0))
hex_prism = bpy.context.object

# Optionally, you can set the name of the object
hex_prism.name = "Hexagonal Prism"
