# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_code_in_Blender__generate_cylinder_and_move_to_location__0__0__5" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using code in Blender, generate cylinder and move to location (0, 0, 5).

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 5))
