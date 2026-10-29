# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_script_create_a_cube_of_tubular_bioinspired_material_with_tub" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender script create a cube of tubular bioinspired material with tubule layers Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_tubules = 20  # Total number of tubules
layer_thickness_value = 0.04  # Thickness of the layer around each tubule

def tubule_factory():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    grid_dim = math.ceil(math.sqrt(total_tubules))
    spacing_value = 2 / grid_dim
    start_position = -1 + spacing_value / 2
    tubule_positions = [
        (start_position + (i % grid_dim) * spacing_value,
         start_position + (i // grid_dim) * spacing_value)
        for i in range(total_tubules)
    ]
    created_layers = []
    for x, y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness_value, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        bool_mod = cube_base.modifiers.new(name=f"Sub_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_tubule
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        layer_bool_mod = inner_tubule.modifiers.new(name=f"Layer_Sub_{x}_{y}", type='BOOLEAN')
        layer_bool_mod.operation = 'DIFFERENCE'
        layer_bool_mod.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_bool_mod.name)
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        created_layers.append(inner_tubule)
    if created_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in created_layers:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = created_layers[0]
        bpy.ops.object.join()
        final_tubule_shell = bpy.context.object
        final_tubule_shell.name = "Final_Tubule_Shell"

tubule_factory()
