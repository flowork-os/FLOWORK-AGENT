# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_script_that_makes_a_tubular_bioinspired_structure_with_noisy" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender script that makes a tubular bioinspired structure with noisy tubule placement Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular structure
number_of_tubules = 16  # Total number of tubules
max_noise = 0.08  # Maximum noise deviation

# Function to create the tubular structure
def generate_tubules(count=number_of_tubules, noise=max_noise):
    # Function to create a cube and subtract tubules from it
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dimension
    initial_offset = -1 + spacing / 2
    
    # Calculate positions for tubules
    positions = [(initial_offset + (i % grid_dimension) * spacing,
                  initial_offset + (i // grid_dimension) * spacing)
                 for i in range(count)]
    
    # Introduce random noise to positions
    noisy_positions = [(x + random.uniform(-noise, noise),
                        y + random.uniform(-noise, noise)) for x, y in positions]
    
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        # Create and apply Boolean modifier
        bool_modifier = main_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Remove the tubule object after subtraction
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the generation of tubules
generate_tubules()
