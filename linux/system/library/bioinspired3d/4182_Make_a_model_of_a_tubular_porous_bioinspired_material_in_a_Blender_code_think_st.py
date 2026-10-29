# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_a_tubular_porous_bioinspired_material_in_a_Blender_code_think_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of a tubular porous bioinspired material in a Blender code think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tubule_total = 9

def build_tubule_structure(total):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object

    grid_dim = math.ceil(math.sqrt(total))
    spacing = 2 / grid_dim
    start_pos = -1 + spacing / 2

    positions = [(start_pos + (i % grid_dim) * spacing,
                  start_pos + (i // grid_dim) * spacing)
                 for i in range(total)]

    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object

        boolean_modifier = base_cube.modifiers.new(name=f"Subtraction_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

build_tubule_structure(tubule_total)
