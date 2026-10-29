# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_script_that_makes_dog_bowl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender script that makes dog bowl

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def add_bowl(radius, depth, position, bowl_name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = bowl_name
    return obj

outer_bowl = add_bowl(1.5, 0.5, (0, 0, 0), 'Bowl_Outer')
inner_bowl = add_bowl(1.2, 0.4, (0, 0, 0.05), 'Bowl_Inner')

outer_bowl_mod = outer_bowl.modifiers.new(name='CarveLip', type='BOOLEAN')
outer_bowl_mod.operation = 'DIFFERENCE'
outer_bowl_mod.object = inner_bowl

bpy.context.view_layer.objects.active = outer_bowl
bpy.ops.object.modifier_apply(modifier='CarveLip')

bpy.data.objects.remove(inner_bowl, do_unlink=True)
