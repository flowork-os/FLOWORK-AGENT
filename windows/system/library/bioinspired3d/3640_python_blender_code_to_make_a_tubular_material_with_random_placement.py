# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_make_a_tubular_material_with_random_placement" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to make a tubular material with random placement

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
total_tubules = 20
jitter_amount = 0.06


def construct_tubules(total=20, jitter=0.06):
    # Builds a grid of tubules with noise in their positions.
    # Process:
    # 1. Create a cube.
    # 2. Position tubules in a grid.
    # 3. Apply noise to positions.
    # 4. Use Boolean modifiers for subtraction.
    
    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    
    # Calculate grid size
    grid_size = math.ceil(math.sqrt(total))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    # Generate positions for tubules
    positions = [(offset + (i % grid_size) * spacing,
                   offset + (i // grid_size) * spacing)
                 for i in range(total)]
    
    # Introduce random noise
    noisy_positions = [(x + random.uniform(-jitter, jitter),
                        y + random.uniform(-jitter, jitter)) for x, y in positions]
    
    # Subtract each tubule from the cube
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        # Add Boolean modifier
        boolean_modifier = cube_base.modifiers.new(name=f"Boolean_Subtract_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule
        
        # Apply the modifier
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        
        # Clean up the tubule object
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute tubule construction
construct_tubules(total_tubules, jitter_amount)
