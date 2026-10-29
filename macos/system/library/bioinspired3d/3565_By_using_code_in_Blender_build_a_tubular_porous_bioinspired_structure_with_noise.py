# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_code_in_Blender_build_a_tubular_porous_bioinspired_structure_with_noise" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using code in Blender build a tubular porous bioinspired structure with noise

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular arrangement
number_of_tubules = 16  # Total number of tubules
max_noise = 0.07  # Maximum deviation for tubule positions


def generate_tubules(count=16, noise=0.07):
    # Function to create a grid of tubules with random noise.
    # Steps:
    # 1. Initialize a cube.
    # 2. Position tubules in a grid.
    # 3. Add noise to positions.
    # 4. Use Boolean operations to cut out tubules from the cube.

    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object

    # Determine grid size and spacing
    grid_dim = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2

    # Create positions for the tubules
    positions = [(offset + (i % grid_dim) * spacing, offset + (i // grid_dim) * spacing) for i in range(count)]

    # Apply random noise to positions
    perturbed_positions = [(x + random.uniform(-noise, noise), y + random.uniform(-noise, noise)) for x, y in positions]

    # Create and subtract tubules from the cube
    for x, y in perturbed_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object

        # Boolean modifier to subtract tubule from cube
        bool_modifier = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule

        # Apply the Boolean modifier
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        # Remove tubule object
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
generate_tubules(number_of_tubules, max_noise)
