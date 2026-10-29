# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_a_tubular_structure_with_random_placement_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of a tubular structure with random placement using Blender code

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the number of tubules and noise
total_tubules = 18
random_noise = 0.1

def setup_tubules(count, noise):
    # Create a base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    grid_dim = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dim
    start_offset = -1 + spacing / 2
    base_positions = [(start_offset + (i % grid_dim) * spacing, start_offset + (i // grid_dim) * spacing) for i in range(count)]
    varied_positions = [(x + random.uniform(-noise, noise), y + random.uniform(-noise, noise)) for x, y in base_positions]
    for x, y in varied_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        current_tubule = bpy.context.object
        bool_mod = cube_base.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = current_tubule
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(current_tubule, do_unlink=True)

setup_tubules(total_tubules, random_noise)
