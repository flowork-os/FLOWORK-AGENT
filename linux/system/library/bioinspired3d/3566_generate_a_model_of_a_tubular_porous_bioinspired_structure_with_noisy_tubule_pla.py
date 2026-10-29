# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_a_tubular_porous_bioinspired_structure_with_noisy_tubule_pla" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of a tubular porous bioinspired structure with noisy tubule placement using Blender code

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule configuration
total_tubules = 20  # Number of tubules
noise_variation = 0.1  # Noise factor for tubule placement


def create_tubular_structure(tubule_count=20, noise=0.1):
    # Constructs a cube with a grid of tubules and applies noise.
    # Procedure:
    # 1. Add a cube.
    # 2. Layout tubules in a grid.
    # 3. Introduce noise to positions.
    # 4. Use Boolean modifiers to cut out tubules.

    # Add a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object

    # Set up grid dimensions
    grid_dimension = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_dimension
    initial_offset = -1 + spacing / 2

    # Calculate positions for tubules
    tubule_positions = [(initial_offset + (i % grid_dimension) * spacing, initial_offset + (i // grid_dimension) * spacing) for i in range(tubule_count)]

    # Add noise to positions
    jittered_positions = [(x + random.uniform(-noise, noise), y + random.uniform(-noise, noise)) for x, y in tubule_positions]

    # Subtract tubules from the cube
    for x, y in jittered_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object

        # Boolean modifier to subtract tubule from the cube
        modifier = cube_object.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule

        # Apply the modifier
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=modifier.name)

        # Delete the tubule
        bpy.data.objects.remove(tubule, do_unlink=True)

# Generate the structure
create_tubular_structure(total_tubules, noise_variation)
