# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_Blender_code__build_a_tubular_bioinspired_structure_with_jittered_placement" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with Blender code, build a tubular bioinspired structure with jittered placement Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the number of tubules
total_tubules = 25
random_noise = 0.1

def build_tubules(total=25, noise=0.1):
    # Function to create a grid of tubules with randomized positions.
    # 1. Create the base cube.
    # 2. Arrange tubules in a grid.
    # 3. Add noise to the positions.
    # 4. Subtract the tubules using Boolean.
    
    # Create the initial cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(total))
    gap = 2 / grid_dimension
    start_pos = -1 + gap / 2
    
    # Calculate positions for the tubules
    positions = [(start_pos + (i % grid_dimension) * gap,
                   start_pos + (i // grid_dimension) * gap)
                 for i in range(total)]
    
    # Apply random noise to positions
    altered_positions = [(x + random.uniform(-noise, noise),
                          y + random.uniform(-noise, noise)) for x, y in positions]
    
    # Subtract each tubule from the cube
    for x, y in altered_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        current_tubule = bpy.context.object
        
        bool_mod = cube_object.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = current_tubule
        
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Execute the tubule building process
build_tubules(total_tubules, random_noise)
