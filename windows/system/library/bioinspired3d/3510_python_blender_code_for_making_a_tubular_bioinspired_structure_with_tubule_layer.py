# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_making_a_tubular_bioinspired_structure_with_tubule_layer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for making a tubular bioinspired structure with tubule layers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular formation
number_of_tubules = 16  # Total count of tubules
layer_width = 0.05  # Thickness of the layer surrounding each tubule

def generate_tubules():
    # Function to create a cube with a grid of tubules surrounded by a layer.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(number_of_tubules))
    spacing_distance = 2 / grid_dimension
    initial_offset = -1 + spacing_distance / 2
    positions = [
        (initial_offset + (i % grid_dimension) * spacing_distance,
         initial_offset + (i // grid_dimension) * spacing_distance)
        for i in range(number_of_tubules)
    ]
    layers = []
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_cylinder = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(x, y, 0))
        outer_cylinder = bpy.context.object
        bool_modifier = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_cylinder
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        layer_modifier = inner_cylinder.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_cylinder
        bpy.context.view_layer.objects.active = inner_cylinder
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)
        bpy.data.objects.remove(outer_cylinder, do_unlink=True)
        layers.append(inner_cylinder)
    if layers:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in layers:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = layers[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Tubule_Layer_Shell"

# Create the tubular structure
generate_tubules()
