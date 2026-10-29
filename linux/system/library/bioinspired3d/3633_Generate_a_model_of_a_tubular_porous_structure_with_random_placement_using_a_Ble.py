# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_tubular_porous_structure_with_random_placement_using_a_Ble" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a tubular porous structure with random placement using a Blender script

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define configuration values
tube_count = 18
random_noise = 0.09

def build_tubule_structure(count, noise):
    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_obj = bpy.context.object
    grid_count = math.ceil(math.sqrt(count))
    spacing = 2 / grid_count
    offset = -1 + spacing / 2

    # Calculate positions
    positions = [(offset + (i % grid_count) * spacing,
                  offset + (i // grid_count) * spacing)
                 for i in range(count)]

    # Add noise to positions
    noisy_positions = [(x + random.uniform(-noise, noise),
                        y + random.uniform(-noise, noise))
                       for x, y in positions]

    # Create tubules and apply boolean modifier
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule_obj = bpy.context.object
        bool_mod = cube_obj.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule_obj
        bpy.context.view_layer.objects.active = cube_obj
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule_obj, do_unlink=True)

# Build the structure
build_tubule_structure(tube_count, random_noise)
