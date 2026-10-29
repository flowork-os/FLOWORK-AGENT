# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_rectangular_prism_in_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate rectangular prism in a Blender code

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a rectangular prism (cuboid)
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
# Scale the cube to form a rectangular prism
bpy.ops.transform.resize(value=(2, 1, 3))
