# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_Python_script__create_a_model_of_a_tubular_porous_bioinspired_m" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender Python script, create a model of a tubular porous bioinspired material with jittered placement. think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the structure of tubules
num_tubules = 15  # Total count of tubules
max_noise = 0.08  # Maximum deviation for noise

def generate_tubules(count=15, noise_level=0.08):
    # Function to create a grid of tubules with random noise
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    positions = [(offset + (i % grid_dim) * spacing, offset + (i // grid_dim) * spacing) for i in range(count)]
    noisy_positions = [(x + random.uniform(-noise_level, noise_level), y + random.uniform(-noise_level, noise_level)) for x, y in positions]
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        current_tubule = bpy.context.object
        bool_modifier = base_cube.modifiers.new(name="SubtractTubule_{:.2f}_{:.2f}".format(x, y), type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Create the tubular structure
generate_tubules(num_tubules, max_noise)
