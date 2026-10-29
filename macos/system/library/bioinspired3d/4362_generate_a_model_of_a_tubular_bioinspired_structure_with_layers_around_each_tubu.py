# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_a_tubular_bioinspired_structure_with_layers_around_each_tubu" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of a tubular bioinspired structure with layers around each tubule in python blender code Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 16  # Total number of tubules
layer_width = 0.05  # Thickness of layer surrounding each tubule

def generate_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(num_tubules))
    spacing_distance = 2 / grid_dimension
    initial_offset = -1 + spacing_distance / 2
    
    tubule_positions = [(initial_offset + (i % grid_dimension) * spacing_distance,
                         initial_offset + (i // grid_dimension) * spacing_distance)
                        for i in range(num_tubules)]
    
    processed_layers = []
    
    for x, y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule_obj = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(x, y, 0))
        outer_tubule_obj = bpy.context.object
        
        bool_modifier = base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tubule_obj
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        layer_modifier = inner_tubule_obj.modifiers.new(name=f"Bool_Layer_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule_obj
        bpy.context.view_layer.objects.active = inner_tubule_obj
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)

        bpy.data.objects.remove(outer_tubule_obj, do_unlink=True)
        
        processed_layers.append(inner_tubule_obj)
        
    if processed_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in processed_layers:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = processed_layers[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Layer_Shell"

generate_tubules()
