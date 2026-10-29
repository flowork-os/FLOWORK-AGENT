# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_blender_code_make_a_model_of_a_cube_of_tubular_bioinspired_material_w" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a blender code make a model of a cube of tubular bioinspired material with random placement.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular design
total_tubules = 12  # Number of tubules to create
noise_factor = 0.1  # Noise factor for positioning

def build_tubules(num_tubules, noise):
    # Create a base cube and arrange tubules in a grid with noise
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    step = 2 / grid_size
    start = -1 + step / 2

    positions = [(start + (i % grid_size) * step, 
                  start + (i // grid_size) * step)
                 for i in range(num_tubules)]

    noisy_positions = [(x + random.uniform(-noise, noise), 
                        y + random.uniform(-noise, noise)) for x, y in positions]

    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object

        bool_mod = cube.modifiers.new(name="Bool_{:.2f}_{:.2f}".format(x, y), type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule

        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the tubule creation
build_tubules(total_tubules, noise_factor)
