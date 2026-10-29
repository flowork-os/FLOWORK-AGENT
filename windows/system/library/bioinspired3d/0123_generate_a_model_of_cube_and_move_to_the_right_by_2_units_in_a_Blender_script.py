# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_cube_and_move_to_the_right_by_2_units_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of cube and move to the right by 2 units in a Blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))

# Move the cube to the right by 2 units
bpy.ops.transform.translate(value=(2, 0, 0))
