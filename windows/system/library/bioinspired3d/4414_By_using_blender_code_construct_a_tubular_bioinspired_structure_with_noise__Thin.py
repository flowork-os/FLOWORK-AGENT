# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_code_construct_a_tubular_bioinspired_structure_with_noise__Thin" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender code construct a tubular bioinspired structure with noise. Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 16  # Total tubules in the structure
max_noise = 0.07  # Maximum deviation for tubule placement

def generate_tubules(count=16, noise=0.07):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dimension
    initial_offset = -1 + spacing / 2
    
    positions = [(initial_offset + (i % grid_dimension) * spacing,
                  initial_offset + (i // grid_dimension) * spacing)
                 for i in range(count)]
    
    randomized_positions = [(x + random.uniform(-noise, noise),
                             y + random.uniform(-noise, noise)) for x, y in positions]
    
    for x, y in randomized_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        bool_modifier = base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        bpy.data.objects.remove(tubule, do_unlink=True)

generate_tubules(num_tubules, max_noise)
