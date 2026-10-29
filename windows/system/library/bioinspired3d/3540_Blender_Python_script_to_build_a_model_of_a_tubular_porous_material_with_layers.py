# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_to_build_a_model_of_a_tubular_porous_material_with_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script to build a model of a tubular porous material with layers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
count_of_tubules = 25  # Number of tubules in the structure
layer_thickness_value = 0.06  # Thickness of the layer surrounding each tubule

def construct_tubular_structure():
    # Function to create a cube and arrange tubules in a grid.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    grid_dim = math.ceil(math.sqrt(count_of_tubules))
    spacing_value = 2 / grid_dim
    offset_value = -1 + spacing_value / 2

    positions = [(offset_value + (i % grid_dim) * spacing_value,
                  offset_value + (i // grid_dim) * spacing_value)
                 for i in range(count_of_tubules)]

    tubule_objects = []

    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness_value, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object

        bool_modifier = cube_base.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        layer_bool_modifier = inner_tubule.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_bool_modifier.operation = 'DIFFERENCE'
        layer_bool_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_bool_modifier.name)

        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        tubule_objects.append(inner_tubule)

    if tubule_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in tubule_objects:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = tubule_objects[0]
        bpy.ops.object.join()
        final_tubular_structure = bpy.context.object
        final_tubular_structure.name = "Tubular_Structure"

# Execute the construction of the tubular structure
construct_tubular_structure()
