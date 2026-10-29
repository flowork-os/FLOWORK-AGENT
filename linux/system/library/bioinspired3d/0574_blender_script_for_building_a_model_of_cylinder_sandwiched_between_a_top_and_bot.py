# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_building_a_model_of_cylinder_sandwiched_between_a_top_and_bot" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for building a model of cylinder sandwiched between a top and bottom rectangular prism

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create the bottom rectangular prism
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, -1))
bottom_prism = bpy.context.object
bottom_prism.scale[0] = 1  # Width
bottom_prism.scale[1] = 1  # Depth
bottom_prism.scale[2] = 0.5  # Height

# Create the cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=2, location=(0, 0, 0))
cylinder = bpy.context.object

# Create the top rectangular prism
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
top_prism = bpy.context.object
top_prism.scale[0] = 1  # Width
top_prism.scale[1] = 1  # Depth
top_prism.scale[2] = 0.5  # Height
