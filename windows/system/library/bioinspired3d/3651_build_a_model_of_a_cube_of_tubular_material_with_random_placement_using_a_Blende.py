# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_a_cube_of_tubular_material_with_random_placement_using_a_Blende" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of a cube of tubular material with random placement using a Blender script

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Settings for the tubular configuration
num_of_tubules = 15  # Number of tubules
max_noise_offset = 0.06  # Noise offset for positioning

def create_tubule_grid(tubule_count, noise):
    # Function to create a grid of tubules with noise effects
    cube_obj = bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_position = -1 + spacing / 2
    
    positions = [(start_position + (i % grid_size) * spacing, start_position + (i // grid_size) * spacing) for i in range(tubule_count)]
    noisy_positions = [(x + random.uniform(-noise, noise), y + random.uniform(-noise, noise)) for x, y in positions]
    
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        boolean_modifier = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the creation of the grid
create_tubule_grid(num_of_tubules, max_noise_offset)
