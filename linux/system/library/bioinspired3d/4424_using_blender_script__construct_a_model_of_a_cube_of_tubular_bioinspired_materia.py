# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_script__construct_a_model_of_a_cube_of_tubular_bioinspired_materia" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender script, construct a model of a cube of tubular bioinspired material with jittered placement. think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 15  # Total number of tubules in the structure
max_noise = 0.07  # Maximum noise deviation applied to tubule positions

def generate_tubules(count=15, noise_level=0.07):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dim
    initial_offset = -1 + spacing / 2
    
    positions = [(initial_offset + (i % grid_dim) * spacing, 
                  initial_offset + (i // grid_dim) * spacing) 
                 for i in range(count)]
    
    noisy_positions = [(x + random.uniform(-noise_level, noise_level), 
                        y + random.uniform(-noise_level, noise_level)) for x, y in positions]
    
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        boolean_modifier = base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule
        
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        
        bpy.data.objects.remove(tubule, do_unlink=True)

generate_tubules(num_tubules, max_noise)
