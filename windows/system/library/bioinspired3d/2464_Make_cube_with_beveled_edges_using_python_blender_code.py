# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_cube_with_beveled_edges_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make cube with beveled edges using python blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))

# Get the active object (the cube we just created)
cube = bpy.context.active_object

# Add a bevel modifier
bevel_modifier = cube.modifiers.new(name="Bevel", type='BEVEL')
bevel_modifier.width = 0.2  # Set the bevel width
bevel_modifier.segments = 10  # Set the number of segments for the bevel

# Apply the bevel modifier
bpy.ops.object.modifier_apply(modifier=bevel_modifier.name)
