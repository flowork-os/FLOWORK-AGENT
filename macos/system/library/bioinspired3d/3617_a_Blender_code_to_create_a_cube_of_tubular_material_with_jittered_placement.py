# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_to_create_a_cube_of_tubular_material_with_jittered_placement" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code to create a cube of tubular material with jittered placement.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the parameters for the structure
number_of_tubules = 25  # Total tubules
random_noise = 0.06  # Amount of noise


def setup_tubular_structure(tubule_count=25, noise_amount=0.06):
    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    grid_dim = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_dim
    offset_start = -1 + spacing / 2

    # Calculate tubule positions
    positions = [(offset_start + (i % grid_dim) * spacing,
                  offset_start + (i // grid_dim) * spacing)
                 for i in range(tubule_count)]

    # Apply random noise
    positions_with_noise = [(x + random.uniform(-noise_amount, noise_amount),
                              y + random.uniform(-noise_amount, noise_amount)) for x, y in positions]

    # Subtract tubules from the cube
    for x, y in positions_with_noise:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule_cylinder = bpy.context.object

        # Create Boolean modifier
        boolean_modifier = cube_base.modifiers.new(name='TubeSubtract', type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule_cylinder

        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)

        bpy.data.objects.remove(tubule_cylinder, do_unlink=True)

# Execute the creation of the tubular structure
setup_tubular_structure(number_of_tubules, random_noise)
