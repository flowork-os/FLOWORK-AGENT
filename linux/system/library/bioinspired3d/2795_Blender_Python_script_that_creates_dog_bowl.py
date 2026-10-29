# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_creates_dog_bowl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that creates dog bowl

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=0.2, location=(0, 0, 0))
outer_shell = bpy.context.object
outer_shell.name = "Bowl Outer"

bpy.ops.mesh.primitive_cylinder_add(radius=1.3, depth=0.1, location=(0, 0, 0.1))
inner_cylinder = bpy.context.object
inner_cylinder.name = "Bowl Inner"

boolean_modifier = outer_shell.modifiers.new(name="Subtract Inner", type='BOOLEAN')
boolean_modifier.operation = 'DIFFERENCE'
boolean_modifier.object = inner_cylinder
bpy.context.view_layer.objects.active = outer_shell

bpy.ops.object.modifier_apply(modifier="Subtract Inner")

bpy.data.objects.remove(inner_cylinder, do_unlink=True)
