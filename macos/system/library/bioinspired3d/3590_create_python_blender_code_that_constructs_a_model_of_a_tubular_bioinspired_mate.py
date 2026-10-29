# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_python_blender_code_that_constructs_a_model_of_a_tubular_bioinspired_mate" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create python blender code that constructs a model of a tubular bioinspired material with noisy tubule placement.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular structure
num_tubules = 15  # Total number of tubules in the structure
max_noise = 0.07  # Maximum noise deviation applied to tubule positions

def generate_tubules(count=15, noise_level=0.07):
    # Function to create a cube with a grid of tubules with noise placement.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid dimensions for tubules
    grid_dim = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dim
    initial_offset = -1 + spacing / 2
    
    # Calculate positions for tubules in the grid
    positions = [(initial_offset + (i % grid_dim) * spacing, 
                  initial_offset + (i // grid_dim) * spacing) 
                 for i in range(count)]
    
    # Add random noise to each position
    noisy_positions = [(x + random.uniform(-noise_level, noise_level), 
                        y + random.uniform(-noise_level, noise_level)) for x, y in positions]
    
    # Subtract cylinders from the cube
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        # Create Boolean modifier for subtraction
        boolean_modifier = base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule
        
        # Apply the Boolean modifier
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        
        # Remove the cylinder after applying the modifier
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
generate_tubules(num_tubules, max_noise)
