# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_rectangular_prism_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of rectangular prism using code in Blender

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a rectangular prism (cuboid)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))

# Scale the cube to form a rectangular prism
bpy.ops.transform.resize(value=(2, 1, 3))  # Adjust the values as needed for dimensions
