# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_for_generating_hollow_elliptical_cylinder_by_subtracting_a" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script for generating hollow elliptical cylinder by subtracting a smaller elliptical cylinder from the center of a larger one

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create the larger elliptical cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=3, location=(0, 0, 0))
large_cylinder = bpy.context.object
large_cylinder.name = "Large_Elliptical_Cylinder"

# Scale to create an ellipse
large_cylinder.scale[0] = 1.5  # X scale
large_cylinder.scale[1] = 1.0   # Y scale

# Create the smaller elliptical cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=3, location=(0, 0, 0))
small_cylinder = bpy.context.object
small_cylinder.name = "Small_Elliptical_Cylinder"

# Scale to create an ellipse
small_cylinder.scale[0] = 1.2  # X scale
small_cylinder.scale[1] = 0.8   # Y scale

# Select both cylinders
bpy.ops.object.select_all(action='DESELECT')
large_cylinder.select_set(True)
small_cylinder.select_set(True)

# Set the active object to the large cylinder
bpy.context.view_layer.objects.active = large_cylinder

# Perform the difference operation
bpy.ops.object.modifier_add(type='BOOLEAN')
bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
bpy.context.object.modifiers["Boolean"].object = small_cylinder
bpy.ops.object.modifier_apply(modifier="Boolean")

# Delete the small cylinder
bpy.data.objects.remove(small_cylinder)
