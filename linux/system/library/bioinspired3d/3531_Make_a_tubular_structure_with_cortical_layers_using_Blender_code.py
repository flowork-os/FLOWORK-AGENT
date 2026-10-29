# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_tubular_structure_with_cortical_layers_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a tubular structure with cortical layers using Blender code

import bpy
import math

# Clear the existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define parameters for the tubular structure
num_tubules = 9  # Total number of tubules
layer_thickness = 0.07  # Thickness of layer surrounding each tubule

def construct_tubules():
    # Create a cube as the starting object
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    # Calculate grid arrangement for tubules
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    # Generate positions for tubules within the grid
    positions = [(start_offset + (i % grid_size) * spacing,
                  start_offset + (i // grid_size) * spacing)
                 for i in range(num_tubules)]
    
    # List to hold processed tubule layers
    processed_layers = []
    
    # Iterate through positions to create and subtract cylinders from the cube
    for x, y in positions:
        # Create inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object

        # Create outer tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        
        # Apply Boolean subtraction to remove the inner tubule from the cube
        cube_modifier = cube.modifiers.new(name=f'bool_{x}_{y}', type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        # Apply Boolean subtraction to create the hollow shell around the tubule
        shell_modifier = inner_tubule.modifiers.new(name=f'shell_{x}_{y}', type='BOOLEAN')
        shell_modifier.operation = 'DIFFERENCE'
        shell_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=shell_modifier.name)

        # Remove the outer tubule object after subtraction
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        
        # Store the processed inner tubule for merging
        processed_layers.append(inner_tubule)
    
    # Merge all processed layers into a single object
    if processed_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in processed_layers:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = processed_layers[0]
        bpy.ops.object.join()
        final_object = bpy.context.object
        final_object.name = 'Layer_Shell'

# Execute the function to construct the tubular structure
construct_tubules()
