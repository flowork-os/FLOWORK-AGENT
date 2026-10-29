# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_makes_a_tubular_bioinspired_structure_with_layers_around_e" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that makes a tubular bioinspired structure with layers around each tubule

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
total_tubules = 12  # Number of tubules
layer_width = 0.04  # Thickness of the layer around each tubule

# Function to create the tubular structure

def create_tubular_structure():
    # Constructs a cube with arranged tubules and layers.
    # Steps:
    # 1. Create a cube.
    # 2. Place tubules in a grid.
    # 3. Generate inner and outer tubules at each grid position.
    # 4. Apply Boolean modifiers to remove inner tubules from the cube.
    # 5. Create a hollow shell around the tubules.

    # Initialize a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    # Determine grid size
    grid_dim = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    
    # Calculate positions for tubules
    positions = [(offset + (i % grid_dim) * spacing, 
                   offset + (i // grid_dim) * spacing) 
                  for i in range(total_tubules)]
    
    # List for storing processed tubules
    processed_tubules = []
    
    # Iterate over positions to create and subtract tubules
    for position_x, position_y in positions:
        # Create an inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(position_x, position_y, 0))
        inner_tubule = bpy.context.object

        # Create an outer tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(position_x, position_y, 0))
        outer_tubule = bpy.context.object
        
        # Boolean modifier to subtract inner tubule from the cube
        cube_modifier = main_cube.modifiers.new(name=f"Cube_Bool_{{position_x}}_{{position_y}}", type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        # Boolean modifier for shell subtraction
        shell_modifier = inner_tubule.modifiers.new(name=f"Shell_Bool_{{position_x}}_{{position_y}}", type='BOOLEAN')
        shell_modifier.operation = 'DIFFERENCE'
        shell_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=shell_modifier.name)

        # Clean up the outer tubule after processing
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        
        # Store the inner tubule
        processed_tubules.append(inner_tubule)
    
    # Merge all processed tubules into one object
    if processed_tubules:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in processed_tubules:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = processed_tubules[0]
        bpy.ops.object.join()
        final_tubule_shell = bpy.context.object
        final_tubule_shell.name = "Final_Tubule_Shell"

# Invoke the creation of the tubular structure
create_tubular_structure()
