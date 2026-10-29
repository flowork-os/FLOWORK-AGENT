# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_Blender_code_generate_a_model_of_a_tubular_bioinspired_structure_with_rando" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with Blender code generate a model of a tubular bioinspired structure with random placement think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the structure
num_tubules = 20
noise_level = 0.07

def build_tubules(tubule_count, noise):
    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_pos = -1 + spacing / 2
    positions = [(start_pos + (i % grid_size) * spacing, start_pos + (i // grid_size) * spacing) for i in range(tubule_count)]
    noisy_positions = [(x + random.uniform(-noise, noise), y + random.uniform(-noise, noise)) for x, y in positions]
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object
        bool_mod = cube.modifiers.new(name=f"SubtractTube_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tube
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tube, do_unlink=True)

build_tubules(num_tubules, noise_level)
