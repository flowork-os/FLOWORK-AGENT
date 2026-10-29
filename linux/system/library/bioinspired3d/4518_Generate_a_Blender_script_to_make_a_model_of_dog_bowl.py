# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_script_to_make_a_model_of_dog_bowl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender script to make a model of dog bowl

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj

outer_bowl = create_cylinder(1.5, 0.2, (0, 0, 0), "Bowl Outer")
inner_bowl = create_cylinder(1.3, 0.1, (0, 0, 0.1), "Bowl Inner")

bool_mod = outer_bowl.modifiers.new(name="Hollow Effect", type='BOOLEAN')
bool_mod.operation = 'DIFFERENCE'
bool_mod.object = inner_bowl
bpy.context.view_layer.objects.active = outer_bowl
bpy.ops.object.modifier_apply(modifier="Hollow Effect")

bpy.data.objects.remove(inner_bowl, do_unlink=True)
