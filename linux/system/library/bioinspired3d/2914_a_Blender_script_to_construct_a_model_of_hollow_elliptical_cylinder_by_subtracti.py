# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_construct_a_model_of_hollow_elliptical_cylinder_by_subtracti" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to construct a model of hollow elliptical cylinder by subtracting a smaller elliptical cylinder from the center of a larger one.

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
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=3, location=(0, 0, 0))
small_cylinder = bpy.context.object
small_cylinder.name = "Small_Elliptical_Cylinder"
small_cylinder.scale[0] = 0.75  # Scale X for ellipse
small_cylinder.scale[1] = 0.5    # Scale Y for ellipse

# Select both cylinders for boolean operation
bpy.ops.object.select_all(action='DESELECT')
large_cylinder.select_set(True)
small_cylinder.select_set(True)

# Set the active object to the large cylinder
bpy.context.view_layer.objects.active = large_cylinder

# Add a boolean modifier to the large cylinder
bool_modifier = large_cylinder.modifiers.new(name="Boolean", type='BOOLEAN')
bool_modifier.operation = 'DIFFERENCE'
bool_modifier.use_self = False
bool_modifier.object = small_cylinder

# Apply the boolean modifier
bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

# Delete the small cylinder
bpy.data.objects.remove(small_cylinder, do_unlink=True)
