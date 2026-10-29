# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_code_that_creates_a_model_of_a_tubular_porous_bioinspired_struc" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender code that creates a model of a tubular porous bioinspired structure with layers around each tubule Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 16  # Total number of tubes in the structure
layer_thickness = 0.05  # Thickness of the layer around each tube

def build_tubular_structure():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object

    grid_dim = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2

    tube_positions = [(offset + (i % grid_dim) * spacing,
                       offset + (i // grid_dim) * spacing)
                      for i in range(num_tubules)]

    created_layers = []

    for x, y in tube_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object

        bool_modifier = main_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tube
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        shell_modifier = inner_tube.modifiers.new(name=f"Shell_{x}_{y}", type='BOOLEAN')
        shell_modifier.operation = 'DIFFERENCE'
        shell_modifier.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=shell_modifier.name)

        bpy.data.objects.remove(outer_tube, do_unlink=True)

        created_layers.append(inner_tube)

    if created_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for layer in created_layers:
            layer.select_set(True)
        bpy.context.view_layer.objects.active = created_layers[0]
        bpy.ops.object.join()
        final_structure = bpy.context.object
        final_structure.name = "Tubular_Structure"

build_tubular_structure()
