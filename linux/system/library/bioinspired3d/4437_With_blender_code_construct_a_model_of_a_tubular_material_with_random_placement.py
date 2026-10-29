# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_code_construct_a_model_of_a_tubular_material_with_random_placement" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender code construct a model of a tubular material with random placement think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the model
number_of_tubules = 18  # Total tubules
noise_offset = 0.09  # Noise level

def build_tubule_structure(tubule_count, noise_factor):
    # Add a base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    grid_dim = math.ceil(math.sqrt(tubule_count))
    gap = 2 / grid_dim
    start_pos = -1 + gap / 2

    # Determine positions for tubules
    positions = [(start_pos + (i % grid_dim) * gap,
                  start_pos + (i // grid_dim) * gap)
                 for i in range(tubule_count)]

    # Introduce noise to positions
    noisy_coords = [(x + random.uniform(-noise_factor, noise_factor),
                     y + random.uniform(-noise_factor, noise_factor)) for x, y in positions]

    for x, y in noisy_coords:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        bool_mod = cube_base.modifiers.new(name="SubtractTubule", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Build the structure with tubules
build_tubule_structure(number_of_tubules, noise_offset)
