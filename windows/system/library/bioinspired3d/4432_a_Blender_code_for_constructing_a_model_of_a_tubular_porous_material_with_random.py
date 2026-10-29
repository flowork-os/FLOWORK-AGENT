# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_constructing_a_model_of_a_tubular_porous_material_with_random" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for constructing a model of a tubular porous material with random placement think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tubule_num = 22
noise_variance = 0.06

def build_tubules(tubule_num, noise_variance):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_num))
    spacing = 2 / grid_size
    start = -1 + spacing / 2
    positions = [(start + (i % grid_size) * spacing, start + (i // grid_size) * spacing) for i in range(tubule_num)]
    
    for x, y in positions:
        x_noise = x + random.uniform(-noise_variance, noise_variance)
        y_noise = y + random.uniform(-noise_variance, noise_variance)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_noise, y_noise, 0))
        tubule = bpy.context.object
        bool_mod = cube.modifiers.new(name='Subtract', type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

build_tubules(tubule_num, noise_variance)
