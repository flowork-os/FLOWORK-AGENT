# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_code_build_a_tubular_bioinspired_material_with_noisy_tubule_placem" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender code build a tubular bioinspired material with noisy tubule placement think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Structure parameters
count_tubules = 18  # Number of tubules
noise_factor = 0.09  # Noise deviation

def build_tubular_structure(count, noise):
    # Create a cube as the base
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    # Calculate positions with grid arrangement
    tube_positions = [(offset + (i % grid_size) * spacing,
                       offset + (i // grid_size) * spacing)
                      for i in range(count)]

    # Add noise to the positions
    jittered_positions = [(x + random.uniform(-noise, noise),
                           y + random.uniform(-noise, noise)) for x, y in tube_positions]

    # Subtract each tube from the cube
    for x, y in jittered_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object

        # Create and apply Boolean modifier
        boolean_mod = base_cube.modifiers.new(name='TubeBoolean', type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tube

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

        bpy.data.objects.remove(tube, do_unlink=True)

# Generate the tubular structure
build_tubular_structure(count_tubules, noise_factor)
