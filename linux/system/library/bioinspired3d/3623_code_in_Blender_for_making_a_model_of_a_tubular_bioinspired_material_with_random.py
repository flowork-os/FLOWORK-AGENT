# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_for_making_a_model_of_a_tubular_bioinspired_material_with_random" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender for making a model of a tubular bioinspired material with random placement.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule parameters
count = 25
noise_amount = 0.06

def create_tubule_structure(tubule_count, noise):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    positions = [(start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing) for i in range(tubule_count)]
    noisy_positions = [(x + random.uniform(-noise, noise), y + random.uniform(-noise, noise)) for x, y in positions]
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        bool_modifier = cube.modifiers.new(name="Tubule_{:.2f}_{:.2f}".format(x, y), type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the structure
create_tubule_structure(count, noise_amount)
