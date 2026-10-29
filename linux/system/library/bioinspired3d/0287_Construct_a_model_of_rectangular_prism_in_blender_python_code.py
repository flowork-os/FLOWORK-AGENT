# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_rectangular_prism_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of rectangular prism in blender python code

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a rectangular prism (cuboid)
bpy.ops.mesh.primitive_cube_add(size=2)  # Create a cube with a size of 2
prism = bpy.context.object  # Get the created cube object

# Scale the cube to form a rectangular prism
prism.scale[0] = 1.5  # Scale X
prism.scale[1] = 2.0  # Scale Y
prism.scale[2] = 0.5  # Scale Z
