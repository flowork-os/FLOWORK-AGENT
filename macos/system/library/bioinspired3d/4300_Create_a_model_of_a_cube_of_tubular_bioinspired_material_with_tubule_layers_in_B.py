# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_a_cube_of_tubular_bioinspired_material_with_tubule_layers_in_B" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of a cube of tubular bioinspired material with tubule layers in Blender code Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure configuration
num_tubes = 20  # Total number of tubes
layer_width_value = 0.06  # Width of the layer around each tube

def construct_tubular_grid():
    # Start with a cube and create tubules
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_anchor = bpy.context.object
    grid_dim = math.ceil(math.sqrt(num_tubes))
    separation = 2 / grid_dim
    offset_start = -1 + separation / 2
    tube_positions = [(offset_start + (i % grid_dim) * separation, offset_start + (i // grid_dim) * separation) for i in range(num_tubes)]
    created_layers = []
    for tube_x, tube_y in tube_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(tube_x, tube_y, 0))
        inner_tube = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width_value, depth=2, location=(tube_x, tube_y, 0))
        outer_tube = bpy.context.object
        cube_bool_mod = cube_anchor.modifiers.new(name=f"Cube_Bool_{tube_x}_{tube_y}", type='BOOLEAN')
        cube_bool_mod.operation = 'DIFFERENCE'
        cube_bool_mod.object = inner_tube
        bpy.context.view_layer.objects.active = cube_anchor
        bpy.ops.object.modifier_apply(modifier=cube_bool_mod.name)
        layer_bool_mod = inner_tube.modifiers.new(name=f"Layer_Bool_{tube_x}_{tube_y}", type='BOOLEAN')
        layer_bool_mod.operation = 'DIFFERENCE'
        layer_bool_mod.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=layer_bool_mod.name)
        bpy.data.objects.remove(outer_tube, do_unlink=True)
        created_layers.append(inner_tube)
    if created_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for layer in created_layers:
            layer.select_set(True)
        bpy.context.view_layer.objects.active = created_layers[0]
        bpy.ops.object.join()
        final_structure = bpy.context.object
        final_structure.name = "Final_Tubular_Structure"

construct_tubular_grid()
