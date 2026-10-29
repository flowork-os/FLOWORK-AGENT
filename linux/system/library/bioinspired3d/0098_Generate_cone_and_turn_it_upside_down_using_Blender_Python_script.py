# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_cone_and_turn_it_upside_down_using_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate cone and turn it upside down using Blender Python script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cone
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1, depth=2, location=(0, 0, 0))

# Get the created cone object
cone = bpy.context.active_object

# Rotate the cone 180 degrees around the X-axis to turn it upside down
cone.rotation_euler[0] = math.radians(180)
