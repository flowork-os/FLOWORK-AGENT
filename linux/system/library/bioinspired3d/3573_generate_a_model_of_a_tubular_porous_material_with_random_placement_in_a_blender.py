# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_a_tubular_porous_material_with_random_placement_in_a_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of a tubular porous material with random placement in a blender code

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
num_cylinders = 25  # Total number of cylinders
position_noise = 0.08  # Noise applied to cylinder positions

def create_cylinder_grid(cylinder_count, noise_level):
    # Creates a cube and subtracts cylinders arranged in a grid with noise
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(cylinder_count))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2

    positions = [(offset + (i % grid_dim) * spacing, 
                  offset + (i // grid_dim) * spacing)
                 for i in range(cylinder_count)]

    noisy_positions = [(x + random.uniform(-noise_level, noise_level), 
                        y + random.uniform(-noise_level, noise_level)) for x, y in positions]

    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        cylinder = bpy.context.object

        bool_modifier = base_cube.modifiers.new(name="Cylinder_{:.2f}_{:.2f}".format(x, y), type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = cylinder

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        bpy.data.objects.remove(cylinder, do_unlink=True)

# Create the grid of cylinders
create_cylinder_grid(num_cylinders, position_noise)
