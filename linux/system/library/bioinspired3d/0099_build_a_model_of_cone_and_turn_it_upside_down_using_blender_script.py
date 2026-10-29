# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_cone_and_turn_it_upside_down_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of cone and turn it upside down using blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cone
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1, depth=2, location=(0, 0, 0))

# Rotate the cone upside down
bpy.ops.transform.rotate(value=math.radians(180), orient_axis='X')
