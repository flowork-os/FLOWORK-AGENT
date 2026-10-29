# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_cone_and_scale_down_by_50__using_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate cone and scale down by 50% using blender python code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cone
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1, depth=2, location=(0, 0, 0))

# Scale down the cone by 50%
bpy.ops.transform.resize(value=(0.5, 0.5, 0.5))
