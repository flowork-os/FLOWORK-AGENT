# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_python_blender_code_that_builds_a_tubular_bioinspired_material_with_random" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write python blender code that builds a tubular bioinspired material with random placement

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_tubules = 16  # Number of tubules in the grid
max_noise = 0.07  # Noise range for positioning

def generate_tubules(count=16, noise=0.07):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dim
    start = -1 + spacing / 2
    positions = [(start + (i % grid_dim) * spacing, start + (i // grid_dim) * spacing) for i in range(count)]
    jittered_positions = [(x + random.uniform(-noise, noise), y + random.uniform(-noise, noise)) for x, y in positions]
    for x, y in jittered_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        current_tubule = bpy.context.object
        bool_mod = main_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = current_tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(current_tubule, do_unlink=True)

generate_tubules(total_tubules, max_noise)
