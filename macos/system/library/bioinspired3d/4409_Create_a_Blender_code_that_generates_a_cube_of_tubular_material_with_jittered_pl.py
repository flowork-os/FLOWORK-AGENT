# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_Blender_code_that_generates_a_cube_of_tubular_material_with_jittered_pl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a Blender code that generates a cube of tubular material with jittered placement think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tubule_quantity = 16  # Number of tubules
jitter_amount = 0.1  # Noise deviation

def generate_tubules(count, jitter):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dimension
    start_offset = -1 + spacing / 2
    positions = [(start_offset + (i % grid_dimension) * spacing, start_offset + (i // grid_dimension) * spacing) for i in range(count)]
    noisy_positions = [(x + random.uniform(-jitter, jitter), y + random.uniform(-jitter, jitter)) for x, y in positions]
    for pos in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos[0], pos[1], 0))
        current_tubule = bpy.context.object
        bool_modifier = base_cube.modifiers.new(name=f"Bool_{pos[0]}_{pos[1]}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(current_tubule, do_unlink=True)

generate_tubules(tubule_quantity, jitter_amount)
