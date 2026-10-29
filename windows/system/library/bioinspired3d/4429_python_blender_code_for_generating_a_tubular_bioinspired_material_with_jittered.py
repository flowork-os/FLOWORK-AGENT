# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_generating_a_tubular_bioinspired_material_with_jittered" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for generating a tubular bioinspired material with jittered placement. Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tubule_quantity = 16  # Total number of tubules
random_noise = 0.07  # Maximum noise deviation

def generate_tubules(quantity, noise_val):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(quantity))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    positions = [(offset + (i % grid_dim) * spacing, offset + (i // grid_dim) * spacing) for i in range(quantity)]
    noisy_positions = [(x + random.uniform(-noise_val, noise_val), y + random.uniform(-noise_val, noise_val)) for x, y in positions]
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

generate_tubules(tubule_quantity, random_noise)
