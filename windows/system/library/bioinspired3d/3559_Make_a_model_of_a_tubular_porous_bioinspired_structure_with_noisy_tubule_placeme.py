# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_a_tubular_porous_bioinspired_structure_with_noisy_tubule_placeme" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of a tubular porous bioinspired structure with noisy tubule placement in blender script

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
number_of_tubules = 22
noise_range = 0.09

def create_tubular_grid(tubule_count, noise_variation):
    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_pos = -1 + spacing / 2
    
    # Generate grid positions
    positions = [(start_pos + (i % grid_size) * spacing, 
                  start_pos + (i // grid_size) * spacing) 
                 for i in range(tubule_count)]
    
    # Apply noise to positions
    noisy_positions = [(x + random.uniform(-noise_variation, noise_variation), 
                        y + random.uniform(-noise_variation, noise_variation)) for x, y in positions]
    
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        boolean_modifier = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
create_tubular_grid(number_of_tubules, noise_range)
