# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_tubular_porous_bioinspired_material_using_code_in_Blender_think_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a tubular porous bioinspired material using code in Blender think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

count_of_tubules = 25  # Total number of tubules

def construct_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(count_of_tubules))
    spacing_dist = 2 / grid_dim
    offset_start = -1 + spacing_dist / 2
    
    positions_list = [(offset_start + (i % grid_dim) * spacing_dist,
                        offset_start + (i // grid_dim) * spacing_dist)
                       for i in range(count_of_tubules)]
    
    for pos_x, pos_y in positions_list:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        tubule_object = bpy.context.object

        boolean_mod = main_cube.modifiers.new(name=f"Cut_{pos_x}_{pos_y}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tubule_object

        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

        bpy.data.objects.remove(tubule_object, do_unlink=True)

construct_tubules()
