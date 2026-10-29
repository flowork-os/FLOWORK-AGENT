# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_blender_code_that_makes_a_tubular_bioinspired_structure_with_tubule_l" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a blender code that makes a tubular bioinspired structure with tubule layers. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular formation
number_of_tubules = 16  # Total number of tubules in the structure
layer_width = 0.05  # Thickness of layer surrounding each tubule

def build_tubules():
    # Function to create a cube with a grid of tubules surrounded by a layer.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(number_of_tubules))
    gap = 2 / grid_dimension
    initial_offset = -1 + gap / 2
    
    # Calculate positions for tubules in the grid
    tubule_positions = [(initial_offset + (i % grid_dimension) * gap, 
                         initial_offset + (i // grid_dimension) * gap) 
                        for i in range(number_of_tubules)]
    
    tubular_layers = []
    
    for pos_x, pos_y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_tube = bpy.context.object
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(pos_x, pos_y, 0))
        outer_tube = bpy.context.object
        
        # Apply Boolean modifier to subtract inner tube from the cube
        bool_modifier = main_cube.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tube
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Apply Boolean modifier to create hollow shell around the inner tube
        shell_modifier = inner_tube.modifiers.new(name=f"Shell_{pos_x}_{pos_y}", type='BOOLEAN')
        shell_modifier.operation = 'DIFFERENCE'
        shell_modifier.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=shell_modifier.name)
        
        bpy.data.objects.remove(outer_tube, do_unlink=True)
        tubular_layers.append(inner_tube)
    
    # Merge all tubular layers into a single object
    if tubular_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for layer in tubular_layers:
            layer.select_set(True)
        bpy.context.view_layer.objects.active = tubular_layers[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Tubular_Structure"

# Build the tubular structure
build_tubules()
