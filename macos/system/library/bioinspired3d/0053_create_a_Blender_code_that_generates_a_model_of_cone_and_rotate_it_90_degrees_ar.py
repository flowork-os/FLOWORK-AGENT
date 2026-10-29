# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_Blender_code_that_generates_a_model_of_cone_and_rotate_it_90_degrees_ar" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a Blender code that generates a model of cone and rotate it 90 degrees around the Y axis.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cone
bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(0, 0, 0))

# Rotate the cone 90 degrees around the Y axis
bpy.ops.transform.rotate(value=math.radians(90), orient_axis='Y')
