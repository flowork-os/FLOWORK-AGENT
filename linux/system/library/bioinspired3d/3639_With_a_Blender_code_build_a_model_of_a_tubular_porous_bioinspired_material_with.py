# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_code_build_a_model_of_a_tubular_porous_bioinspired_material_with" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender code build a model of a tubular porous bioinspired material with noise.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the structure of tubules
num_tubules = 16  # Total number of tubules
max_noise = 0.08  # Maximum deviation for noise


def generate_tubules(count=16, noise=0.08):
    # Constructs a grid of tubules with randomized positions.
    # Steps:
    # 1. Initialize a cube.
    # 2. Distribute tubules in a grid.
    # 3. Introduce noise to positions.
    # 4. Subtract tubules using Boolean modifiers.
    
    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid layout
    grid_dim = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dim
    offset_start = -1 + spacing / 2
    
    # Calculate positions for tubules
    tubule_positions = [(offset_start + (i % grid_dim) * spacing,
                         offset_start + (i // grid_dim) * spacing) 
                        for i in range(count)]
    
    # Add noise to positions
    randomized_positions = [(x + random.uniform(-noise, noise),
                             y + random.uniform(-noise, noise)) for x, y in tubule_positions]
    
    # Subtract each tubule from the cube
    for x, y in randomized_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        current_tubule = bpy.context.object
        
        # Set up Boolean modifier
        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule
        
        # Apply the modifier
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Remove the tubule
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Create the structure
generate_tubules(num_tubules, max_noise)
