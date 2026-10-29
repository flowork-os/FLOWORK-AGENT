# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_python_code_construct_a_tubular_porous_bioinspired_material_with_no" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender python code construct a tubular porous bioinspired material with noisy tubule placement.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters defining the number of tubular structures and noise level
number_of_tubules = 16  # Total count of tubules
noise_variation = 0.07  # Maximum deviation for noise in positions

# Function to create a grid of tubules with noise

def generate_tubules(count=16, noise_level=0.07):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dim
    initial_offset = -1 + spacing / 2
    
    # Calculate positions in a grid
    positions = [(initial_offset + (i % grid_dim) * spacing, 
                  initial_offset + (i // grid_dim) * spacing) 
                 for i in range(count)]
    
    # Introduce random noise to positions
    noisy_positions = [(x + random.uniform(-noise_level, noise_level), 
                        y + random.uniform(-noise_level, noise_level)) for x, y in positions]
    
    # Create and subtract tubules from the cube
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        # Set up Boolean modifier for subtraction
        bool_modifier = main_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        
        # Apply the modifier
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Clean up the tubule object
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the tubule generation
generate_tubules(number_of_tubules, noise_variation)
