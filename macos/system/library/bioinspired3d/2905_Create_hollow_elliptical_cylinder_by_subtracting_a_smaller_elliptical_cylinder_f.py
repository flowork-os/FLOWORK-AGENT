# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_hollow_elliptical_cylinder_by_subtracting_a_smaller_elliptical_cylinder_f" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create hollow elliptical cylinder by subtracting a smaller elliptical cylinder from the center of a larger one using blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create the larger elliptical cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=3, location=(0, 0, 0))
large_cylinder = bpy.context.object
large_cylinder.name = "Large_Elliptical_Cylinder"
large_cylinder.scale[0] = 1.5  # Scale X for ellipse
large_cylinder.scale[1] = 1.0   # Scale Y for ellipse

# Create the smaller elliptical cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=3, location=(0, 0, 0))
small_cylinder = bpy.context.object
small_cylinder.name = "Small_Elliptical_Cylinder"
small_cylinder.scale[0] = 0.75  # Scale X for ellipse
small_cylinder.scale[1] = 0.5    # Scale Y for ellipse

# Select both cylinders
bpy.ops.object.select_all(action='DESELECT')
large_cylinder.select_set(True)
small_cylinder.select_set(True)

# Set the active object to the large cylinder
bpy.context.view_layer.objects.active = large_cylinder

# Boolean modifier to subtract the smaller cylinder from the larger one
bpy.ops.object.modifier_add(type='BOOLEAN')
bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
bpy.context.object.modifiers["Boolean"].object = small_cylinder

# Apply the modifier
bpy.ops.object.modifier_apply(modifier="Boolean")

# Delete the smaller cylinder
bpy.data.objects.remove(small_cylinder)
