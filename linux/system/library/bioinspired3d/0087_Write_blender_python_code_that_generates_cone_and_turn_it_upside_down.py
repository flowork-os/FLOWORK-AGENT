# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_python_code_that_generates_cone_and_turn_it_upside_down" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender python code that generates cone and turn it upside down.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cone
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1, depth=2, location=(0, 0, 0))

# Get the active object (the cone we just created)
cone = bpy.context.active_object

# Rotate the cone 180 degrees around the X-axis to turn it upside down
cone.rotation_euler[0] = math.radians(180)
