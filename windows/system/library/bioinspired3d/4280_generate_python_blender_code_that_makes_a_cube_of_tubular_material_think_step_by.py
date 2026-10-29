# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_python_blender_code_that_makes_a_cube_of_tubular_material_think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate python blender code that makes a cube of tubular material think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule structure parameters
count_tubules = 25  # Number of tubules
ellipse_scale = 1.1  # Stretch factor
radius_tubule = 0.05  # Radius of the tubules

def construct_tubule_grid(tubule_count, scale_factor, tubule_radius):
    # Function to create a grid of tubules and subtract them from a cube.
    # 1. Start with a cube.
    # 2. Arrange tubules in a grid.
    # 3. Subtract using Boolean modifiers.
    
    # Create a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    # Calculate grid dimensions
    grid_dim = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    
    # Generate positions for tubules
    tubule_positions = [(offset + (i % grid_dim) * spacing, offset + (i // grid_dim) * spacing) for i in range(tubule_count)]
    
    # Subtract each tubule from the cube
    for pos in tubule_positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=tubule_radius, depth=3, location=(x, y, 0))
        current_tubule = bpy.context.object
        current_tubule.scale[0] *= scale_factor  # Apply scale factor
        
        # Create and apply Boolean modifier
        boolean_modifier = main_cube.modifiers.new(name=f"Remove_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = current_tubule
        
        # Apply the modifier
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        
        # Remove the tubule from the scene
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Execute the function to create the grid of tubules
construct_tubule_grid(count_tubules, ellipse_scale, radius_tubule)
