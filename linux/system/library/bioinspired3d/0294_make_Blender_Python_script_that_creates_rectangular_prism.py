# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_Blender_Python_script_that_creates_rectangular_prism" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make Blender Python script that creates rectangular prism

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a rectangular prism (cuboid)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))

# Scale the cube to create a rectangular prism
bpy.ops.transform.resize(value=(2, 1, 3))  # Change the values to your desired dimensions
