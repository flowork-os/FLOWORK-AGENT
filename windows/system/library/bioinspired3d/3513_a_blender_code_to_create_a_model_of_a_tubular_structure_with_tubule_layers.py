# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_to_create_a_model_of_a_tubular_structure_with_tubule_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code to create a model of a tubular structure with tubule layers.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular structure
count_of_tubules = 21  # Total number of tubules
layer_thickness_value = 0.07  # Thickness of the layer around each tubule

def create_tubule_structure():
    # Function to create a grid of tubules
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(count_of_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    positions = [
        (start_offset + (i % grid_size) * spacing,
         start_offset + (i // grid_size) * spacing)
        for i in range(count_of_tubules)
    ]
    created_layers = []
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness_value, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        bool_modifier = main_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        layer_modifier = inner_tubule.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        created_layers.append(inner_tubule)
    if created_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in created_layers:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = created_layers[0]
        bpy.ops.object.join()
        final_structure = bpy.context.object
        final_structure.name = "Final_Tubule_Structure"

# Generate the tubular structure
create_tubule_structure()
