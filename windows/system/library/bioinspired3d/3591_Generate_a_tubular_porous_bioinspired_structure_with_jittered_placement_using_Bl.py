# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_tubular_porous_bioinspired_structure_with_jittered_placement_using_Bl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a tubular porous bioinspired structure with jittered placement using Blender Python script

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
total_tubules = 20  # Number of tubules to create
noise_variation = 0.05  # Noise variation applied to tubule positions

def create_tubular_structure(tubule_count, noise_amount):
    # This function constructs a cube and arranges tubules with noise.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    
    # Calculate grid size for arrangement
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    # Calculate positions for the tubules
    positions = [(offset + (i % grid_size) * spacing, 
                  offset + (i // grid_size) * spacing) 
                 for i in range(tubule_count)]
    
    # Introduce noise to positions
    positions_with_noise = [(x + random.uniform(-noise_amount, noise_amount), 
                             y + random.uniform(-noise_amount, noise_amount)) for x, y in positions]
    
    # Subtract each tubule from the cube
    for x, y in positions_with_noise:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        # Boolean modifier setup
        boolean_mod = cube_object.modifiers.new(name=f"Subtraction_{x}_{y}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tubule
        
        # Apply the modifier
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)
        
        # Clean up the tubule object
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute tubule creation
create_tubular_structure(total_tubules, noise_variation)
