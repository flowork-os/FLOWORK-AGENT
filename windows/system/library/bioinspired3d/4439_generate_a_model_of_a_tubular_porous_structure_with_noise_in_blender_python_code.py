# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_a_tubular_porous_structure_with_noise_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of a tubular porous structure with noise in blender python code Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 20  # Total number of tubules
noise_level = 0.05  # Noise deviation for tubule positions

def create_structure(num_tubules=20, noise=0.05):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    positions = [(offset + (i % grid_size) * spacing,
                  offset + (i // grid_size) * spacing)
                 for i in range(num_tubules)]

    noisy_positions = [(x + random.uniform(-noise, noise),
                        y + random.uniform(-noise, noise)) for x, y in positions]

    for pos_x, pos_y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        tubule = bpy.context.object

        bool_mod = base_cube.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        bpy.data.objects.remove(tubule, do_unlink=True)

create_structure(num_tubules, noise_level)
