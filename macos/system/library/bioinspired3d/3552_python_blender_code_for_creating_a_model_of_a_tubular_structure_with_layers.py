# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_creating_a_model_of_a_tubular_structure_with_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for creating a model of a tubular structure with layers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure configuration
number_of_tubules = 12  # Total number of tubules
layer_width = 0.04  # Width of the layer surrounding each tubule

def generate_tubular_grid():
    # Create a cube as the base
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object

    # Determine grid layout
    grid_dim = math.ceil(math.sqrt(number_of_tubules))
    spacing = 2 / grid_dim
    start_offset = -1 + spacing / 2

    # Calculate positions for each tubule
    tubule_positions = [(start_offset + (i % grid_dim) * spacing,
                         start_offset + (i // grid_dim) * spacing)
                        for i in range(number_of_tubules)]

    # List to hold created tubules
    tubule_objects = []

    for pos_x, pos_y in tubule_positions:
        # Create inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_tubule = bpy.context.object

        # Create outer tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(pos_x, pos_y, 0))
        outer_tubule = bpy.context.object

        # Apply Boolean modifier to subtract inner from cube
        bool_modifier = base_cube.modifiers.new(name=f"Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        # Apply Boolean modifier to create the hollow shell
        hollow_modifier = inner_tubule.modifiers.new(name=f"Hollow_{pos_x}_{pos_y}", type='BOOLEAN')
        hollow_modifier.operation = 'DIFFERENCE'
        hollow_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=hollow_modifier.name)

        # Remove the outer tubule
        bpy.data.objects.remove(outer_tubule, do_unlink=True)

        # Store inner tubule
        tubule_objects.append(inner_tubule)

    # Join all inner tubules into a single object
    if tubule_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in tubule_objects:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = tubule_objects[0]
        bpy.ops.object.join()
        final_object = bpy.context.object
        final_object.name = "Tubular_Grid"

# Execute the grid generation
generate_tubular_grid()
