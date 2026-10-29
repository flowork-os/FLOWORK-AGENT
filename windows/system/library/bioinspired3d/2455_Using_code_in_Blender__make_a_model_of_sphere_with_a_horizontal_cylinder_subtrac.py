# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_code_in_Blender__make_a_model_of_sphere_with_a_horizontal_cylinder_subtrac" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using code in Blender, make a model of sphere with a horizontal cylinder subtracted through its center.

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

# Add a boolean modifier to the sphere
bool_modifier = sphere.modifiers.new(name="Boolean", type='BOOLEAN')
bool_modifier.operation = 'DIFFERENCE'
bool_modifier.use_self = False
bool_modifier.object = cylinder

# Apply the boolean modifier
bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

# Delete the cylinder
bpy.data.objects.remove(cylinder, do_unlink=True)
