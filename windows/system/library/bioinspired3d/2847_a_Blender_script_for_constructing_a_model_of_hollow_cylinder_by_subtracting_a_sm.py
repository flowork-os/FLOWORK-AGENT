# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_for_constructing_a_model_of_hollow_cylinder_by_subtracting_a_sm" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script for constructing a model of hollow cylinder by subtracting a smaller cylinder from the center of a larger one.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create the larger cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=2, depth=4, location=(0, 0, 0))
large_cylinder = bpy.context.object
large_cylinder.name = "LargeCylinder"

# Create the smaller cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=4, location=(0, 0, 0))
small_cylinder = bpy.context.object
small_cylinder.name = "SmallCylinder"

# Select both cylinders
bpy.ops.object.select_all(action='DESELECT')
large_cylinder.select_set(True)
small_cylinder.select_set(True)

# Set the active object to the large cylinder
bpy.context.view_layer.objects.active = large_cylinder

# Perform the boolean operation to subtract the smaller cylinder from the larger one
bpy.ops.object.modifier_add(type='BOOLEAN')
boolean_modifier = large_cylinder.modifiers["Boolean"]
boolean_modifier.operation = 'DIFFERENCE'
boolean_modifier.use_self = False
boolean_modifier.object = small_cylinder

# Apply the modifier
bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)

# Delete the small cylinder
bpy.data.objects.remove(small_cylinder)
