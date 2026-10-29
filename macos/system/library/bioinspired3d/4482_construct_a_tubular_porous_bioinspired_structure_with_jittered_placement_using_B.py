# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_tubular_porous_bioinspired_structure_with_jittered_placement_using_B" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a tubular porous bioinspired structure with jittered placement using Blender Python script Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def setup_tubule_structure(total_tubules=24, noise_level=0.09):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_dim
    start_offset = -1 + spacing / 2
    positions = [(start_offset + (i % grid_dim) * spacing, start_offset + (i // grid_dim) * spacing) for i in range(total_tubules)]
    
    for x, y in positions:
        x += random.uniform(-noise_level, noise_level)
        y += random.uniform(-noise_level, noise_level)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        new_tubule = bpy.context.object
        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = new_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(new_tubule, do_unlink=True)

setup_tubule_structure(total_tubules=23, noise_level=0.05)
