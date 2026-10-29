# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_code__make_a_model_of_a_tubular_material_with_random_placement" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender code, make a model of a tubular material with random placement

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set parameters for the tubular formation
num_tubules = 16  # Total tubules in the structure
max_noise = 0.07  # Maximum deviation for tubule placement

def generate_tubules(count=16, noise=0.07):
    # Function to create a grid of tubules with randomized positions.
    # Steps:
    # 1. Generate a base cube.
    # 2. Position tubules in a grid.
    # 3. Introduce noise to positions.
    # 4. Subtract tubules using Boolean operations.
    
    # Create a base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid layout for tubules
    grid_dimension = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dimension
    initial_offset = -1 + spacing / 2
    
    # Calculate positions for tubules
    positions = [(initial_offset + (i % grid_dimension) * spacing,
                  initial_offset + (i // grid_dimension) * spacing)
                 for i in range(count)]
    
    # Add noise to the positions
    randomized_positions = [(x + random.uniform(-noise, noise),
                             y + random.uniform(-noise, noise)) for x, y in positions]
    
    # Subtract tubules from the cube
    for x, y in randomized_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        # Create a Boolean modifier for subtraction
        bool_modifier = base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        
        # Apply the Boolean operation
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Cleanup: remove the tubule object
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
generate_tubules(num_tubules, max_noise)
