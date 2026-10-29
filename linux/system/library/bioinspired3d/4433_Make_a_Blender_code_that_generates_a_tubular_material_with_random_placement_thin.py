# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_Blender_code_that_generates_a_tubular_material_with_random_placement_thin" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a Blender code that generates a tubular material with random placement think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular arrangement
total_tubules = 16  # Number of tubules
jitter_amount = 0.07  # Maximum deviation for noise

# Function to create a grid of tubules with noise
def generate_tubules(count, noise_level):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(count))
    gap = 2 / grid_dimension
    initial_offset = -1 + gap / 2

    positions = [(initial_offset + (i % grid_dimension) * gap,
                  initial_offset + (i // grid_dimension) * gap)
                 for i in range(count)]

    noisy_positions = [(x + random.uniform(-noise_level, noise_level),
                        y + random.uniform(-noise_level, noise_level)) for x, y in positions]

    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        bool_modifier = base_cube.modifiers.new(name="SubtractTubule", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
generate_tubules(total_tubules, jitter_amount)
