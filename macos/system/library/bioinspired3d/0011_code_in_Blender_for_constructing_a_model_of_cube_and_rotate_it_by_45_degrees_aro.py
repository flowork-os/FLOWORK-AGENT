# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_for_constructing_a_model_of_cube_and_rotate_it_by_45_degrees_aro" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender for constructing a model of cube and rotate it by 45 degrees around the Z axis

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2)

# Rotate the cube 45 degrees around the Z axis
bpy.ops.transform.rotate(value=math.radians(45), orient_axis='Z')
