# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_code__make_a_tubular_porous_bioinspired_structure_with_jitter" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender code, make a tubular porous bioinspired structure with jittered placement Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 16  # Total number of tubules
max_noise = 0.08  # Maximum deviation for noise

def generate_tubules(count=16, noise=0.08):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dim
    offset_start = -1 + spacing / 2
    
    tubule_positions = [(offset_start + (i % grid_dim) * spacing,
                         offset_start + (i // grid_dim) * spacing) 
                        for i in range(count)]
    
    randomized_positions = [(x + random.uniform(-noise, noise),
                             y + random.uniform(-noise, noise)) for x, y in tubule_positions]
    
    for x, y in randomized_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        current_tubule = bpy.context.object
        
        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule
        
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        bpy.data.objects.remove(current_tubule, do_unlink=True)

generate_tubules(num_tubules, max_noise)
