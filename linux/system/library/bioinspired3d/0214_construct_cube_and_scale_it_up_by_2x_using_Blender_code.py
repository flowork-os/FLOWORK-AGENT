# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_cube_and_scale_it_up_by_2x_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct cube and scale it up by 2x using Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))

# Scale the cube by 2x
bpy.ops.transform.resize(value=(2, 2, 2))
