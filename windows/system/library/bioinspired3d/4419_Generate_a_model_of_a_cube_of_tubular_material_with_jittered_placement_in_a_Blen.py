# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_cube_of_tubular_material_with_jittered_placement_in_a_Blen" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a cube of tubular material with jittered placement in a Blender script Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular structure
num_tubules = 15  # Total number of tubules
max_noise = 0.08  # Maximum noise deviation

# Function to create a grid of tubules
def generate_tubules(count=15, noise_level=0.08):
    # Initial cube creation and placement of tubules with noise
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dim
    start_pos = -1 + spacing / 2
    
    # Calculate positions for tubules
    positions = [(start_pos + (i % grid_dim) * spacing,
                  start_pos + (i // grid_dim) * spacing)
                 for i in range(count)]
    
    # Apply noise to positions
    noisy_positions = [(x + random.uniform(-noise_level, noise_level),
                        y + random.uniform(-noise_level, noise_level)) for x, y in positions]
    
    # Subtract tubules from the cube
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        mod = base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
generate_tubules(num_tubules, max_noise)
