# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_Blender_Python_script_create_cube_with_beveled_edges" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using Blender Python script create cube with beveled edges.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))

# Get the active object (the cube we just created)
cube = bpy.context.active_object

# Switch to edit mode
bpy.ops.object.mode_set(mode='EDIT')

# Select all edges
bpy.ops.mesh.select_all(action='SELECT')

# Bevel the edges
bpy.ops.mesh.bevel(offset=0.2, segments=10, profile=0.5)

# Switch back to object mode
bpy.ops.object.mode_set(mode='OBJECT')
