# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_a_tubular_bioinspired_structure_in_a_blender_code_Think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of a tubular bioinspired structure in a blender code Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tubule_total = 12  # Total number of tubules

def create_tubule_structure(tubule_total):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    grid_count = math.ceil(math.sqrt(tubule_total))
    spacing = 2 / grid_count
    offset = -1 + spacing / 2
    
    positions = [(offset + (i % grid_count) * spacing,
                  offset + (i // grid_count) * spacing)
                 for i in range(tubule_total)]
    
    for x_pos, y_pos in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_pos, y_pos, 0))
        tubule = bpy.context.object

        boolean_mod = cube.modifiers.new(name=f"Subtract_{x_pos}_{y_pos}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tubule

        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

        bpy.data.objects.remove(tubule, do_unlink=True)

create_tubule_structure(tubule_total)
