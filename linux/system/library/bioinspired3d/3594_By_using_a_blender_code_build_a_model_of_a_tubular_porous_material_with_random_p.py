# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_blender_code_build_a_model_of_a_tubular_porous_material_with_random_p" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a blender code build a model of a tubular porous material with random placement

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular structure
number_of_tubules = 18  # Total number of tubules
noise_deviation = 0.06  # Maximum noise deviation

def construct_tubules(tubule_total, noise_range):
    # Create a cube and add tubules with noise.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(tubule_total))
    spacing = 2 / grid_dimension
    offset = -1 + spacing / 2
    
    positions = [(offset + (i % grid_dimension) * spacing, 
                  offset + (i // grid_dimension) * spacing) 
                 for i in range(tubule_total)]
    
    noisy_positions = [(x + random.uniform(-noise_range, noise_range), 
                        y + random.uniform(-noise_range, noise_range)) for x, y in positions]
    
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        modifier = cube.modifiers.new(name=f"BooleanMod_{x}_{y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute tubule construction
construct_tubules(number_of_tubules, noise_deviation)
