# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_code_create_a_tubular_porous_bioinspired_material_with_noisy_tub" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender code create a tubular porous bioinspired material with noisy tubule placement

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the creation
number_of_tubules = 22
noise_range = 0.06

def setup_tubular_structure(tubule_count, noise):
    # Create a base cube and subtract tubules from it
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
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
        modifier = base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the setup function
setup_tubular_structure(number_of_tubules, noise_range)
