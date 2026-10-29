# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_a_tubular_porous_bioinspired_material_with_layers_using_Blen" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of a tubular porous bioinspired material with layers using Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Setup for the tubular structure
num_tubules = 20  # Number of tubules
layer_thickness = 0.03  # Thickness of the surrounding layer


def create_structure():
    # Function to create a cube and arrange tubules in a grid.
    # Steps:
    # 1. Add a cube as a base object.
    # 2. Generate tubule positions in a grid.
    # 3. Create inner and outer tubules.
    # 4. Use Boolean modifiers to carve out the inner tubules.
    # 5. Form the outer layer by subtracting the outer tubule from the inner one.

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    tubule_positions = [(offset + (i % grid_size) * spacing,
                         offset + (i // grid_size) * spacing)
                        for i in range(num_tubules)]

    created_layers = []

    for pos in tubule_positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object

        cube_boolean = base_cube.modifiers.new(name=f"Cube_Bool_{x}_{y}", type='BOOLEAN')
        cube_boolean.operation = 'DIFFERENCE'
        cube_boolean.object = inner_tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=cube_boolean.name)

        layer_boolean = inner_tube.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_boolean.operation = 'DIFFERENCE'
        layer_boolean.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=layer_boolean.name)

        bpy.data.objects.remove(outer_tube, do_unlink=True)
        created_layers.append(inner_tube)

    if created_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for layer in created_layers:
            layer.select_set(True)
        bpy.context.view_layer.objects.active = created_layers[0]
        bpy.ops.object.join()
        merged_layer = bpy.context.object
        merged_layer.name = "Merged_Layer"

# Execute the structure creation
create_structure()
