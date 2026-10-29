# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_tubular_bioinspired_material_with_cortical_layers_using_Blender_Pyth" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a tubular bioinspired material with cortical layers using Blender Python script think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular design
number_of_tubules = 16  # Number of tubules in the design
layer_width = 0.05  # Width of the layer surrounding each tubule

def construct_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(number_of_tubules))
    spacing = 2 / grid_dimension
    start_position = -1 + spacing / 2
    
    tubule_positions = [(start_position + (i % grid_dimension) * spacing,
                         start_position + (i // grid_dimension) * spacing)
                        for i in range(number_of_tubules)]
    
    created_layers = []
    
    for pos_x, pos_y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_tube = bpy.context.object
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(pos_x, pos_y, 0))
        outer_tube = bpy.context.object
        
        bool_modifier = cube.modifiers.new(name=f"Boolean_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tube
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        layer_modifier = inner_tube.modifiers.new(name=f"Bool_Layer_{pos_x}_{pos_y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)
        
        bpy.data.objects.remove(outer_tube, do_unlink=True)
        created_layers.append(inner_tube)
    
    if created_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for layer in created_layers:
            layer.select_set(True)
        bpy.context.view_layer.objects.active = created_layers[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Final_Shell"

# Execute tubule construction
construct_tubules()
