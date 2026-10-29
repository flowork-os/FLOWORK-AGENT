# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_for_generating_a_model_of_sphere_and_flatten_along_the_Z_a" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script for generating a model of sphere and flatten along the Z axis to 0.3.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a UV sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))

# Get the active object (the sphere we just created)
sphere = bpy.context.active_object

# Scale the sphere along the Z axis
sphere.scale[2] = 0.3

# Apply the scale to make the transformation permanent
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
