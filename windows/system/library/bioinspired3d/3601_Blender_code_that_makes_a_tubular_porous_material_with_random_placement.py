# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_that_makes_a_tubular_porous_material_with_random_placement" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code that makes a tubular porous material with random placement

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define structure parameters
count_tubules = 25  # Number of tubules
noise_level = 0.1  # Noise range

# Function to handle the creation of tubules
def construct_tubules(count, noise):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2

    positions = [(offset + (i % grid_dim) * spacing,
                  offset + (i // grid_dim) * spacing)
                 for i in range(count)]

    positions_with_noise = [(x + random.uniform(-noise, noise),
                             y + random.uniform(-noise, noise)) for x, y in positions]

    for x, y in positions_with_noise:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        bool_mod = main_cube.modifiers.new(name="TubuleBoolean", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute tubule construction
construct_tubules(count_tubules, noise_level)
