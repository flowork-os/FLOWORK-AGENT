# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_for_building_a_model_of_hollow_cylinder_by_subtracting_a_smaller_cy" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code for building a model of hollow cylinder by subtracting a smaller cylinder from the center of a larger one.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create the outer cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))
outer_cylinder = bpy.context.object

# Create the inner cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=2.1, location=(0, 0, 0))
inner_cylinder = bpy.context.object

# Select both cylinders
bpy.ops.object.select_all(action='DESELECT')
outer_cylinder.select_set(True)
inner_cylinder.select_set(True)

# Set the active object to the outer cylinder
bpy.context.view_layer.objects.active = outer_cylinder

# Perform the boolean operation
bpy.ops.object.modifier_add(type='BOOLEAN')
bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
bpy.context.object.modifiers["Boolean"].object = inner_cylinder

# Apply the modifier
bpy.ops.object.modifier_apply(modifier="Boolean")

# Delete the inner cylinder
bpy.data.objects.remove(inner_cylinder)
