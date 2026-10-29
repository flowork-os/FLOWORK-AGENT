# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_blender_code_that_builds_sphere_with_a_horizontal_cylinder_subtracted_thr" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create blender code that builds sphere with a horizontal cylinder subtracted through its center

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
sphere = bpy.context.object

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=2, location=(0, 0, 0))
cylinder = bpy.context.object

# Set the cylinder to be a boolean modifier
bpy.ops.object.select_all(action='DESELECT')
sphere.select_set(True)
bpy.context.view_layer.objects.active = sphere

# Add boolean modifier
bool_mod = sphere.modifiers.new(name="Boolean", type='BOOLEAN')
bool_mod.operation = 'DIFFERENCE'
bool_mod.use_self = False
bool_mod.object = cylinder

# Apply the modifier
bpy.ops.object.modifier_apply(modifier=bool_mod.name)

# Delete the cylinder
bpy.data.objects.remove(cylinder)
