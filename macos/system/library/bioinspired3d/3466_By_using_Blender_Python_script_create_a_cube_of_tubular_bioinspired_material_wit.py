# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_Python_script_create_a_cube_of_tubular_bioinspired_material_wit" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender Python script create a cube of tubular bioinspired material with cortical layers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
number_of_tubules = 16  # Total number of tubules in the structure
layer_width = 0.05  # Thickness of layer surrounding each tubule

def generate_tubules():
    # Function to create tubules in a grid format
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(number_of_tubules))
    gap = 2 / grid_dimension
    initial_offset = -1 + gap / 2
    positions = [(initial_offset + (i % grid_dimension) * gap, initial_offset + (i // grid_dimension) * gap) for i in range(number_of_tubules)]
    layer_objects = []
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(x, y, 0))
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
        layer_objects.append(inner_tube)
    if layer_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in layer_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = layer_objects[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Final_Layer_Shell"

generate_tubules()
