# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_code_build_a_tubular_porous_bioinspired_material_with_jittered_pla" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender code build a tubular porous bioinspired material with jittered placement Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

number_of_tubules = 16  # Total number of tubules in the structure
max_noise = 0.07  # Maximum noise deviation applied to tubule positions

def generate_tubules(count=16, noise=0.07):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dimension
    initial_offset = -1 + spacing / 2

    tubule_positions = [(initial_offset + (i % grid_dimension) * spacing,
                         initial_offset + (i // grid_dimension) * spacing)
                        for i in range(count)]

    jittered_positions = [(x + random.uniform(-noise, noise),
                           y + random.uniform(-noise, noise)) for x, y in tubule_positions]

    for pos_x, pos_y in jittered_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        tubule_object = bpy.context.object

        bool_modifier = cube_object.modifiers.new(name=f"Boolean_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule_object

        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        bpy.data.objects.remove(tubule_object, do_unlink=True)

generate_tubules(number_of_tubules, max_noise)
