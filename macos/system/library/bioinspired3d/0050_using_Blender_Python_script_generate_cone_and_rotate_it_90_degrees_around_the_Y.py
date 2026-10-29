# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_Python_script_generate_cone_and_rotate_it_90_degrees_around_the_Y" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender Python script generate cone and rotate it 90 degrees around the Y axis

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cone
bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(0, 0, 0))

# Rotate the cone 90 degrees around the Y axis
bpy.ops.transform.rotate(value=math.radians(90), orient_axis='Y')
