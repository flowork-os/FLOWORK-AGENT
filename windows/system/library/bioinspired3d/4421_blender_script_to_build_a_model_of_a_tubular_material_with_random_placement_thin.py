# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_to_build_a_model_of_a_tubular_material_with_random_placement_thin" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script to build a model of a tubular material with random placement think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 12  # Total number of tubules
noise_factor = 0.1  # Noise deviation

def build_tubular_structure(tubule_count, noise):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    positions = [(start_offset + (i % grid_size) * spacing,
                  start_offset + (i // grid_size) * spacing)
                 for i in range(tubule_count)]
    
    noisy_positions = [(x + random.uniform(-noise, noise),
                        y + random.uniform(-noise, noise)) for x, y in positions]
    
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        mod = main_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

build_tubular_structure(num_tubules, noise_factor)
