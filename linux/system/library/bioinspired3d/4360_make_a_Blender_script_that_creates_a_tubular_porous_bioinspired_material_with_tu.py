# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_Blender_script_that_creates_a_tubular_porous_bioinspired_material_with_tu" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a Blender script that creates a tubular porous bioinspired material with tubule layers think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the parameters for the tubular arrangement
num_tubules = 12  # Number of tubules
layer_thickness = 0.03  # Thickness of the layer

def tubular_structure():
    cube = bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2

    positions = [(start_offset + (i % grid_size) * spacing, 
                  start_offset + (i // grid_size) * spacing) 
                 for i in range(num_tubules)]

    created_layers = []

    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_cylinder = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_cylinder = bpy.context.object

        bool_modifier = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_cylinder
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        layer_modifier = inner_cylinder.modifiers.new(name=f"LayerBool_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_cylinder
        bpy.context.view_layer.objects.active = inner_cylinder
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)

        bpy.data.objects.remove(outer_cylinder, do_unlink=True)
        created_layers.append(inner_cylinder)

    if created_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for layer in created_layers:
            layer.select_set(True)
        bpy.context.view_layer.objects.active = created_layers[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Final_Tubule_Shell"

# Create the tubular structure
tubular_structure()
