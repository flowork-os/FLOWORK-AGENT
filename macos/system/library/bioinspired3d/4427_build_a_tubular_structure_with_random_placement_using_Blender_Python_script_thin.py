# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_tubular_structure_with_random_placement_using_Blender_Python_script_thin" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a tubular structure with random placement using Blender Python script think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define parameters for the tubular structure
tubule_count = 25  # Total number of tubules
noise_level = 0.09  # Noise applied to tubule positions

def place_tubules(count, noise):
    # Create a cube and arrange tubules with noise.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    positions = [(offset + (i % grid_size) * spacing, 
                  offset + (i // grid_size) * spacing) 
                 for i in range(count)]
    
    noisy_positions = [(x + random.uniform(-noise, noise), 
                        y + random.uniform(-noise, noise)) for x, y in positions]
    
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        boolean_mod = base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Build the tubular structure
place_tubules(tubule_count, noise_level)
