# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_code_create_a_model_of_cube_with_beveled_edges" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender code create a model of cube with beveled edges

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Add a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))

# Select the cube
cube = bpy.context.active_object

# Bevel the edges
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.bevel(offset=0.3, segments=10, profile=0.5)
bpy.ops.object.mode_set(mode='OBJECT')
