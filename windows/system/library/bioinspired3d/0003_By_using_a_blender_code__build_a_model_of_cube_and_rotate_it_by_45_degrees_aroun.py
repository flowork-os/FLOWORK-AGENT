# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_blender_code__build_a_model_of_cube_and_rotate_it_by_45_degrees_aroun" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a blender code, build a model of cube and rotate it by 45 degrees around the Z axis

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2)

# Rotate the cube by 45 degrees around the Z axis
bpy.ops.transform.rotate(value=math.radians(45), orient_axis='Z')
