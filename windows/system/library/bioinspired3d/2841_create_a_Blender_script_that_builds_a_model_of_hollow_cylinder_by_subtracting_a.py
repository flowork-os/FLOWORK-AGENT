# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_Blender_script_that_builds_a_model_of_hollow_cylinder_by_subtracting_a" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a Blender script that builds a model of hollow cylinder by subtracting a smaller cylinder from the center of a larger one

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create the larger cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=2, depth=5, location=(0, 0, 0))
large_cylinder = bpy.context.object

# Create the smaller cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=5, location=(0, 0, 0))
small_cylinder = bpy.context.object

# Select both cylinders
bpy.ops.object.select_all(action='DESELECT')
large_cylinder.select_set(True)
small_cylinder.select_set(True)

# Set the active object to the large cylinder
bpy.context.view_layer.objects.active = large_cylinder

# Perform the boolean operation to subtract the smaller cylinder from the larger one
bpy.ops.object.modifier_add(type='BOOLEAN')
bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
bpy.context.object.modifiers["Boolean"].object = small_cylinder

# Apply the modifier
bpy.ops.object.modifier_apply(modifier="Boolean")

# Delete the smaller cylinder
bpy.data.objects.remove(small_cylinder)
