# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_that_constructs_rectangular_prism" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender that constructs rectangular prism.

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a rectangular prism (cuboid)
bpy.ops.mesh.primitive_cube_add(size=2)  # Create a cube with a size of 2
prism = bpy.context.object

# Scale the cube to form a rectangular prism
prism.scale[0] = 1  # Scale X
prism.scale[1] = 2  # Scale Y
prism.scale[2] = 3  # Scale Z
