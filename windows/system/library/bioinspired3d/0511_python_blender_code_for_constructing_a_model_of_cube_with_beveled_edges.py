# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_constructing_a_model_of_cube_with_beveled_edges" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for constructing a model of cube with beveled edges

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Add a cube
bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))

# Switch to edit mode
bpy.ops.object.mode_set(mode='EDIT')

# Select all edges
bpy.ops.mesh.select_all(action='SELECT')

# Bevel the edges
bpy.ops.mesh.bevel(offset=0.3, segments=10, profile=0.5)

# Switch back to object mode
bpy.ops.object.mode_set(mode='OBJECT')
