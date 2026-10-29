# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_a_cube_of_tubular_bioinspired_material_using_Blender_code_t" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of a cube of tubular bioinspired material using Blender code think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tubule_amount = 20

def create_cuboid_with_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_obj = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(tubule_amount))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    for i in range(tubule_amount):
        x = offset + (i % grid_size) * spacing
        y = offset + (i // grid_size) * spacing
        add_and_subtract_tubule(cube_obj, x, y)

def add_and_subtract_tubule(cube, x_pos, y_pos):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_pos, y_pos, 0))
    tubule_obj = bpy.context.object
    
    bool_mod = cube.modifiers.new(name='Boolean', type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = tubule_obj
    
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    bpy.data.objects.remove(tubule_obj, do_unlink=True)

create_cuboid_with_tubules()
