# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_script__build_a_model_of_a_cube_of_tubular_material_with_jitt" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender script, build a model of a cube of tubular material with jittered placement Think step by step.

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
