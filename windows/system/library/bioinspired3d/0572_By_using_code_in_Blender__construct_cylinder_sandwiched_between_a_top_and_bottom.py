# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_code_in_Blender__construct_cylinder_sandwiched_between_a_top_and_bottom" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using code in Blender, construct cylinder sandwiched between a top and bottom rectangular prism.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create the bottom rectangular prism
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, -1))
bottom_prism = bpy.context.object
bottom_prism.scale[0] = 1  # X scale
bottom_prism.scale[1] = 1  # Y scale
bottom_prism.scale[2] = 0.5  # Z scale

# Create the cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=2, location=(0, 0, 0))
cylinder = bpy.context.object

# Create the top rectangular prism
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
top_prism = bpy.context.object
top_prism.scale[0] = 1  # X scale
top_prism.scale[1] = 1  # Y scale
top_prism.scale[2] = 0.5  # Z scale
