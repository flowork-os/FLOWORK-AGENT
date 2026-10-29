# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_creating_a_model_of_a_tubular_porous_material_with_noise" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for creating a model of a tubular porous material with noise think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tubule_count = 25
noise_variation = 0.05

def create_tubular_structure(tubule_count, noise_variation):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2

    positions = [(start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing) for i in range(tubule_count)]
    positions_with_noise = [(x + random.uniform(-noise_variation, noise_variation), y + random.uniform(-noise_variation, noise_variation)) for x, y in positions]

    for pos in positions_with_noise:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos[0], pos[1], 0))
        tubule = bpy.context.object
        boolean_modifier = cube.modifiers.new(name="Bool_{}".format(pos), type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

create_tubular_structure(tubule_count, noise_variation)
