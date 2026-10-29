# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_code_in_Blender_that_generates_a_model_of_cube_with_beveled_edges" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create code in Blender that generates a model of cube with beveled edges.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Add a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))

# Get the active object (the cube we just created)
cube = bpy.context.active_object

# Add a bevel modifier
bevel_modifier = cube.modifiers.new(name="Bevel", type='BEVEL')
bevel_modifier.width = 0.3  # Set the bevel width
bevel_modifier.segments = 5  # Set the number of segments for the bevel

# Apply the modifier
bpy.ops.object.modifier_apply(modifier=bevel_modifier.name)
