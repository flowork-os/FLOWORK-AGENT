# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_a_tubular_porous_structure_with_cortical_layers_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of a tubular porous structure with cortical layers in Blender Python script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters defining the structure of the tubules
number_of_tubules = 16  # Total number of tubules
layer_width = 0.04  # Thickness of the layer surrounding each tubule

# Function to create the tubular structure

def generate_tubules():
    # Start with a cube as the base object
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine the grid layout based on the number of tubules
    grid_dimension = math.ceil(math.sqrt(number_of_tubules))
    spacing_distance = 2 / grid_dimension
    initial_offset = -1 + spacing_distance / 2
    
    # Calculate positions for each tubule in the grid
    tubule_positions = [(initial_offset + (i % grid_dimension) * spacing_distance,
                         initial_offset + (i // grid_dimension) * spacing_distance)
                        for i in range(number_of_tubules)]
    
    # List to hold the objects for merging later
    shells = []
    
    # Create and subtract each tubule from the cube
    for pos_x, pos_y in tubule_positions:
        # Create the inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_shell = bpy.context.object
        
        # Create the outer tubule layer
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(pos_x, pos_y, 0))
        outer_shell = bpy.context.object
        
        # Apply Boolean modifier to subtract inner tubule from the cube
        bool_modifier = base_cube.modifiers.new(name=f'Bool_{pos_x}_{pos_y}', type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_shell
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Apply Boolean modifier to create the hollow layer
        layer_modifier = inner_shell.modifiers.new(name=f'Layer_Bool_{pos_x}_{pos_y}', type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_shell
        bpy.context.view_layer.objects.active = inner_shell
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)
        
        # Clean up the outer shell after processing
        bpy.data.objects.remove(outer_shell, do_unlink=True)
        shells.append(inner_shell)
    
    # Combine all shells into a single object
    if shells:
        bpy.ops.object.select_all(action='DESELECT')
        for shell in shells:
            shell.select_set(True)
        bpy.context.view_layer.objects.active = shells[0]
        bpy.ops.object.join()
        final_object = bpy.context.object
        final_object.name = 'Final_Tubule_Shell'

# Execute the function to create the structure
generate_tubules()
