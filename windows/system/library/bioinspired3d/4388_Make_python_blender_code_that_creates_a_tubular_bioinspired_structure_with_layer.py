# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_python_blender_code_that_creates_a_tubular_bioinspired_structure_with_layer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make python blender code that creates a tubular bioinspired structure with layers around each tubule. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular design
num_of_tubules = 9  # Total number of tubules
layer_thickness_value = 0.07  # Thickness of the layer surrounding each tubule

def construct_tubular_design():
    # Initialize a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object

    # Calculate grid size
    grid_size = math.ceil(math.sqrt(num_of_tubules))
    tubule_spacing = 2 / grid_size
    start_offset = -1 + tubule_spacing / 2

    # Define positions for the tubules
    tubule_positions = [(start_offset + (i % grid_size) * tubule_spacing,
                         start_offset + (i // grid_size) * tubule_spacing)
                        for i in range(num_of_tubules)]

    created_tubules = []

    for pos_x, pos_y in tubule_positions:
        # Create inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_tubule = bpy.context.object

        # Create outer tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness_value, depth=2, location=(pos_x, pos_y, 0))
        outer_tubule = bpy.context.object

        # Boolean modifier to subtract inner from cube
        bool_modifier = cube_base.modifiers.new(name=f"Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        # Boolean modifier to create hollow shell
        shell_modifier = inner_tubule.modifiers.new(name=f"Shell_{pos_x}_{pos_y}", type='BOOLEAN')
        shell_modifier.operation = 'DIFFERENCE'
        shell_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=shell_modifier.name)

        # Remove the outer tubule
        bpy.data.objects.remove(outer_tubule, do_unlink=True)

        created_tubules.append(inner_tubule)

    # Join all inner tubules into a single object
    if created_tubules:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in created_tubules:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = created_tubules[0]
        bpy.ops.object.join()
        final_tubular_design = bpy.context.object
        final_tubular_design.name = "Tubular_Design"

# Execute the construction of the tubular design
construct_tubular_design()
