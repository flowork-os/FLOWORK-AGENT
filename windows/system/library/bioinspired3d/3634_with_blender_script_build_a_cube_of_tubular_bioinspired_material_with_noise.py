# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_script_build_a_cube_of_tubular_bioinspired_material_with_noise" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender script build a cube of tubular bioinspired material with noise

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular structure
num_tubules = 15  # Number of tubules
max_noise = 0.08  # Maximum noise deviation

def generate_tubules(tubule_count, noise_level):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_dimension
    initial_offset = -1 + spacing / 2

    positions = [(initial_offset + (i % grid_dimension) * spacing, 
                  initial_offset + (i // grid_dimension) * spacing) 
                 for i in range(tubule_count)]
    noisy_positions = [(x + random.uniform(-noise_level, noise_level), 
                        y + random.uniform(-noise_level, noise_level)) for x, y in positions]

    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        current_tubule = bpy.context.object
        bool_modifier = main_cube.modifiers.new(name="Bool_{:.2f}_{:.2f}".format(x, y), type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(current_tubule, do_unlink=True)

generate_tubules(num_tubules, max_noise)
