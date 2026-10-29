# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_a_tubular_porous_structure_with_jittered_placement_in_a_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of a tubular porous structure with jittered placement in a Blender script Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 15  # Total count of tubules
max_noise = 0.07  # Maximum noise deviation for positioning

def generate_tubules(count=15, noise=0.07):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(count))
    interval = 2 / grid_dim
    offset = -1 + interval / 2
    
    positions = [(offset + (i % grid_dim) * interval, offset + (i // grid_dim) * interval) for i in range(count)]
    
    noisy_positions = [(x + random.uniform(-noise, noise), y + random.uniform(-noise, noise)) for x, y in positions]
    
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule_cylinder = bpy.context.object
        
        bool_modifier = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule_cylinder
        
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule_cylinder, do_unlink=True)

generate_tubules(num_tubules, max_noise)
