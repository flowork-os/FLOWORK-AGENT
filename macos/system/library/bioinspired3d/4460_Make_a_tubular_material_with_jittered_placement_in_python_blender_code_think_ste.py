# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_tubular_material_with_jittered_placement_in_python_blender_code_think_ste" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a tubular material with jittered placement in python blender code think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the number of tubules and noise level
num_tubules = 25
noise_level = 0.05

def construct_tubules(n, noise):
    # Function to create a cube and subtract tubules with noise
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(n))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    positions = [(offset + (i % grid_size) * spacing, 
                  offset + (i // grid_size) * spacing) 
                 for i in range(n)]
    noisy_positions = [(x + random.uniform(-noise, noise), 
                        y + random.uniform(-noise, noise)) for x, y in positions]
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        mod = base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure with specified parameters
construct_tubules(num_tubules, noise_level)
