# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_a_cube_of_tubular_material_with_tubule_layers_in_blender_code_T" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of a cube of tubular material with tubule layers in blender code Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
num_tubules = 16  # Total tubules in the structure
layer_thickness = 0.05  # Thickness of the layer surrounding each tubule

def build_tubules():
    # Constructs a cube with tubules arranged in a grid with surrounding layers.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    positions = [(start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing) for i in range(num_tubules)]
    layer_objects = []
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object
        bool_modifier = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        layer_mod = inner_tube.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_mod.operation = 'DIFFERENCE'
        layer_mod.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=layer_mod.name)
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

# Create the tubular structure
build_tubules()
