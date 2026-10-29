# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_code_generate_sphere_and_move_it_upward_by_3_units" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender code generate sphere and move it upward by 3 units

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))

# Move the sphere upward by 3 units
bpy.ops.transform.translate(value=(0, 0, 3))
