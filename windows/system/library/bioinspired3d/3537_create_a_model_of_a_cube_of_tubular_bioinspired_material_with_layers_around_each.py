# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_a_cube_of_tubular_bioinspired_material_with_layers_around_each" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of a cube of tubular bioinspired material with layers around each tubule in a Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular assembly
number_of_tubules = 16  # Total count of tubules
shell_thickness = 0.05  # Thickness of the layer surrounding each tubule


def generate_tubules():
    # Constructs a cube and arranges tubules in a grid pattern.
    # Steps:
    # 1. Initialize a cube.
    # 2. Position tubules in a grid.
    # 3. Create inner and outer tubules for each grid position.
    # 4. Apply Boolean modifiers to subtract inner tubules from the cube.
    # 5. Subtract inner tubule from outer tubule to form the layer.

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(number_of_tubules))
    spacing_distance = 2 / grid_dimension
    initial_offset = -1 + spacing_distance / 2

    positions = [(initial_offset + (i % grid_dimension) * spacing_distance,
                  initial_offset + (i // grid_dimension) * spacing_distance)
                 for i in range(number_of_tubules)]

    shell_objects = []

    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_cylinder = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - shell_thickness, depth=2, location=(x, y, 0))
        outer_cylinder = bpy.context.object

        bool_modifier = main_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_cylinder
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        layer_bool_modifier = inner_cylinder.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_bool_modifier.operation = 'DIFFERENCE'
        layer_bool_modifier.object = outer_cylinder
        bpy.context.view_layer.objects.active = inner_cylinder
        bpy.ops.object.modifier_apply(modifier=layer_bool_modifier.name)

        bpy.data.objects.remove(outer_cylinder, do_unlink=True)
        shell_objects.append(inner_cylinder)

    if shell_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in shell_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = shell_objects[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Final_Shell"

# Create the tubular structure
generate_tubules()
