# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_make_a_tubular_bioinspired_structure_with_random_placemen" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to make a tubular bioinspired structure with random placement.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular arrangement
number_of_tubules = 15  # Total number of tubules
jitter_amount = 0.07  # Maximum deviation in positions

def generate_tubules(count=15, noise=0.07):
    # This function creates a cube and arranges tubules with noise.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dimension
    initial_offset = -1 + spacing / 2
    positions = [(initial_offset + (i % grid_dimension) * spacing, 
                  initial_offset + (i // grid_dimension) * spacing) 
                 for i in range(count)]
    noisy_positions = [(x + random.uniform(-noise, noise), 
                        y + random.uniform(-noise, noise)) for x, y in positions]
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule_cylinder = bpy.context.object
        bool_modifier = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule_cylinder
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule_cylinder, do_unlink=True)

# Create the tubular structure
generate_tubules(number_of_tubules, jitter_amount)
