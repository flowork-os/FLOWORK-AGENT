# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_Blender_code_that_creates_a_model_of_a_tubular_porous_bioinspired_materia" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a Blender code that creates a model of a tubular porous bioinspired material with noise think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 15  # Number of tubes in the structure
max_noise = 0.07  # Maximum deviation for tube positions

def generate_tubules(count=15, noise_level=0.07):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dimension
    initial_offset = -1 + spacing / 2

    positions = [(initial_offset + (i % grid_dimension) * spacing, 
                  initial_offset + (i // grid_dimension) * spacing)
                 for i in range(count)]

    noisy_positions = [(x + random.uniform(-noise_level, noise_level), 
                        y + random.uniform(-noise_level, noise_level)) for x, y in positions]

    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object

        bool_modifier = base_cube.modifiers.new(name="Bool_{:.2f}_{:.2f}".format(x, y), type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tube

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        bpy.data.objects.remove(tube, do_unlink=True)

generate_tubules(num_tubules, max_noise)
