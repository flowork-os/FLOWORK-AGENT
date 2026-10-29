# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_makes_a_model_of_a_tubular_material_with_jittered_placemen" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that makes a model of a tubular material with jittered placement

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the parameters for the tubular formation
count_of_tubules = 25
max_deviation = 0.1


def build_tubule_grid(tubule_count=25, noise=0.1):
    # Constructs a grid of tubules with noise adjustments.
    # Steps:
    # 1. Create a cube.
    # 2. Position tubules in a grid layout.
    # 3. Apply noise to their positions.
    # 4. Subtract tubules from the cube using Boolean modifiers.

    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object

    # Calculate grid dimensions
    grid_dim = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_dim
    start_offset = -1 + spacing / 2

    # Determine positions for the tubules
    positions = [(start_offset + (i % grid_dim) * spacing, start_offset + (i // grid_dim) * spacing) for i in range(tubule_count)]

    # Introduce noise to the positions
    noisy_positions = [(x + random.uniform(-noise, noise), y + random.uniform(-noise, noise)) for x, y in positions]

    # Subtract each tubule from the cube
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        bool_mod = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the creation of the tubule grid
build_tubule_grid(count_of_tubules, max_deviation)
