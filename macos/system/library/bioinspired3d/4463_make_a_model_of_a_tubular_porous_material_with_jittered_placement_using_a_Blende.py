# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_a_tubular_porous_material_with_jittered_placement_using_a_Blende" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of a tubular porous material with jittered placement using a Blender script think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular arrangement
number_of_tubules = 15  # Total number of tubules
max_noise = 0.07  # Maximum noise in positioning

def generate_tubules(count=15, noise=0.07):
    # Constructs a cube and arranges tubules with random noise
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dimension
    offset_start = -1 + spacing / 2

    # Calculate positions for the tubules
    positions = [(offset_start + (i % grid_dimension) * spacing,  
                  offset_start + (i // grid_dimension) * spacing)  
                 for i in range(count)]

    # Introduce noise to positions
    noisy_positions = [(x + random.uniform(-noise, noise),  
                        y + random.uniform(-noise, noise)) for x, y in positions]

    # Subtract each tubule from the cube
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        bool_modifier = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
generate_tubules(number_of_tubules, max_noise)
