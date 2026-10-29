# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_Python_script_that_creates_a_tubular_bioinspired_structure_with" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender Python script that creates a tubular bioinspired structure with noise

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 20
noise_amount = 0.1

def create_tubular_grid(num, noise):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num))
    spacing = 2 / grid_size
    start = -1 + spacing / 2
    coords = [(start + (i % grid_size) * spacing, start + (i // grid_size) * spacing) for i in range(num)]
    jittered_coords = [(x + random.uniform(-noise, noise), y + random.uniform(-noise, noise)) for x, y in coords]
    for x, y in jittered_coords:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        boolean_mod = cube.modifiers.new(name='BooleanMod', type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

create_tubular_grid(num_tubules, noise_amount)
