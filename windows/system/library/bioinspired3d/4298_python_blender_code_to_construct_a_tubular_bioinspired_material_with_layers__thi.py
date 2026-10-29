# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_construct_a_tubular_bioinspired_material_with_layers__thi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to construct a tubular bioinspired material with layers. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular grid
count_tubules = 25  # Number of tubules
thickness_of_layer = 0.03  # Layer thickness

def create_tubular_structure():
    # Start with a cube and subtract tubules
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(count_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(count_tubules)]
    shells = []
    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_cylinder = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - thickness_of_layer, depth=2, location=(pos_x, pos_y, 0))
        outer_cylinder = bpy.context.object
        cube_modifier = base_cube.modifiers.new(name=f"Cube_Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_cylinder
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        layer_modifier = inner_cylinder.modifiers.new(name=f"Layer_Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_cylinder
        bpy.context.view_layer.objects.active = inner_cylinder
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)
        bpy.data.objects.remove(outer_cylinder, do_unlink=True)
        shells.append(inner_cylinder)
    if shells:
        bpy.ops.object.select_all(action='DESELECT')
        for shell in shells:
            shell.select_set(True)
        bpy.context.view_layer.objects.active = shells[0]
        bpy.ops.object.join()
        combined_shell = bpy.context.object
        combined_shell.name = "Combined_Shell"

create_tubular_structure()
