# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_construct_a_model_of_a_tubular_bioinspired_structure_with_no" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to construct a model of a tubular bioinspired structure with noisy tubule placement. Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Settings for the tubular structure
num_tubules = 18
noise_level = 0.07

def create_tubular_structure(tubule_count=18, noise_amount=0.07):
    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    positions = [(offset + (i % grid_size) * spacing,
                   offset + (i // grid_size) * spacing)
                 for i in range(tubule_count)]
    
    noisy_positions = [(x + random.uniform(-noise_amount, noise_amount),
                        y + random.uniform(-noise_amount, noise_amount)) for x, y in positions]
    
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        bool_modifier = base_cube.modifiers.new(name=f"BoolSubtract_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
create_tubular_structure(num_tubules, noise_level)
