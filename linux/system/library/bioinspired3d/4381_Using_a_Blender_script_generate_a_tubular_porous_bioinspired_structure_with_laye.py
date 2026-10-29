# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_Blender_script_generate_a_tubular_porous_bioinspired_structure_with_laye" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a Blender script generate a tubular porous bioinspired structure with layers around each tubule. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular arrangement
num_tubules = 20  # Total number of tubules
layer_thickness = 0.04  # Thickness of the layer around each tubule

def create_structure():
    # Function to create a cube with a grid of tubules and layers.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    grid_count = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_count
    start = -1 + spacing / 2
    tubule_positions = [(start + (i % grid_count) * spacing, start + (i // grid_count) * spacing) for i in range(num_tubules)]
    layer_list = []
    for pos in tubule_positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        cube_object.modifiers.new(name=f"Cube_Bool_{x}_{y}", type='BOOLEAN')
        cube_object.modifiers[-1].operation = 'DIFFERENCE'
        cube_object.modifiers[-1].object = inner_tubule
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=cube_object.modifiers[-1].name)
        inner_tubule.modifiers.new(name=f"Inner_Bool_{x}_{y}", type='BOOLEAN')
        inner_tubule.modifiers[-1].operation = 'DIFFERENCE'
        inner_tubule.modifiers[-1].object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=inner_tubule.modifiers[-1].name)
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        layer_list.append(inner_tubule)
    if layer_list:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in layer_list:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = layer_list[0]
        bpy.ops.object.join()
        final_tubule = bpy.context.object
        final_tubule.name = "Final_Tubule_Layer"

# Run the structure creation
create_structure()
