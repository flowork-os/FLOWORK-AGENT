# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_blender_python_code_that_constructs_a_tubular_structure_with_noise__think_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make blender python code that constructs a tubular structure with noise. think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 25  # Total number of tubules
noise_factor = 0.05  # Maximum noise deviation

def create_structure(num_tubules, noise_factor):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    base_positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(num_tubules)]
    perturbed_positions = [(x + random.uniform(-noise_factor, noise_factor), y + random.uniform(-noise_factor, noise_factor)) for x, y in base_positions]
    for position in perturbed_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(position[0], position[1], 0))
        cylinder = bpy.context.object
        bool_mod = main_cube.modifiers.new(name=f"Subtract_{position[0]}_{position[1]}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = cylinder
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(cylinder, do_unlink=True)

create_structure(num_tubules, noise_factor)
