# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_tubular_porous_bioinspired_structure_with_noisy_tubule_placement_using_a" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a tubular porous bioinspired structure with noisy tubule placement using a Blender code think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
number_of_tubules = 18
random_noise = 0.08

def build_tubule_structure():
    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(number_of_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    # Generate positions for the tubules
    positions = [(start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing) for i in range(number_of_tubules)]
    
    # Introduce random noise to the positions
    for pos in positions:
        x, y = pos
        x += random.uniform(-random_noise, random_noise)
        y += random.uniform(-random_noise, random_noise)
        
        # Create a tubule at the noisy coordinates
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        # Set up Boolean modifier
        bool_modifier = cube_object.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Build the tubule structure
build_tubule_structure()
