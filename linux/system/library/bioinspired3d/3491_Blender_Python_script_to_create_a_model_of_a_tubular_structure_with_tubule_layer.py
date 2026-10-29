# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_to_create_a_model_of_a_tubular_structure_with_tubule_layer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script to create a model of a tubular structure with tubule layers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular model
total_tubules = 25  # Number of tubules
shell_thickness = 0.04  # Thickness of the shell around each tubule

def build_tubular_grid():
    # Function to construct a cube with a grid of tubules surrounded by a shell.
    # Workflow:
    # 1. Create a cube.
    # 2. Place tubules in a grid layout.
    # 3. Generate inner and outer tubules for each grid cell.
    # 4. Use Boolean modifiers to achieve the desired geometry.

    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid dimensions
    grid_dimension = math.ceil(math.sqrt(total_tubules))
    distance = 2 / grid_dimension
    initial_offset = -1 + distance / 2
    
    # Calculate positions for each tubule
    tubule_coords = [
        (initial_offset + (i % grid_dimension) * distance, initial_offset + (i // grid_dimension) * distance)
        for i in range(total_tubules)
    ]
    
    # List to keep track of shell objects
    tubule_shells = []
    
    # Loop through each coordinate to create tubules
    for pos_x, pos_y in tubule_coords:
        # Add inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_cylinder = bpy.context.object
        
        # Add outer tubule layer
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - shell_thickness, depth=2, location=(pos_x, pos_y, 0))
        outer_cylinder = bpy.context.object
        
        # Apply Boolean modifier to cube
        cube_modifier = base_cube.modifiers.new(name=f'Cube_Bool_{pos_x}_{pos_y}', type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_cylinder
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        # Apply Boolean modifier to inner tubule
        shell_modifier = inner_cylinder.modifiers.new(name=f'Shell_Bool_{pos_x}_{pos_y}', type='BOOLEAN')
        shell_modifier.operation = 'DIFFERENCE'
        shell_modifier.object = outer_cylinder
        bpy.context.view_layer.objects.active = inner_cylinder
        bpy.ops.object.modifier_apply(modifier=shell_modifier.name)

        # Remove outer cylinder after processing
        bpy.data.objects.remove(outer_cylinder, do_unlink=True)
        
        # Collect inner tubule for merging
        tubule_shells.append(inner_cylinder)
    
    # Combine all inner tubules into one object
    if tubule_shells:
        bpy.ops.object.select_all(action='DESELECT')
        for shell in tubule_shells:
            shell.select_set(True)
        bpy.context.view_layer.objects.active = tubule_shells[0]
        bpy.ops.object.join()
        final_object = bpy.context.object
        final_object.name = 'Combined_Tubular_Structure'

# Execute the building function
build_tubular_grid()
