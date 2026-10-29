# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_a_cube_of_tubular_bioinspired_material_with_noisy_tubule_placem" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of a cube of tubular bioinspired material with noisy tubule placement using Blender Python script think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubes = 12  # Number of tubes to generate
random_noise = 0.1  # Noise level for tube placement

def create_structure(tube_count, noise_level):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(tube_count))
    tube_spacing = 2 / grid_dimension
    offset = -1 + tube_spacing / 2
    
    positions = [(offset + (i % grid_dimension) * tube_spacing,
                  offset + (i // grid_dimension) * tube_spacing)
                 for i in range(tube_count)]
    
    noisy_positions = [(x + random.uniform(-noise_level, noise_level),
                        y + random.uniform(-noise_level, noise_level)) for x, y in positions]
    
    for pos in noisy_positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object
        
        bool_mod = cube_object.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tube
        
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tube, do_unlink=True)

create_structure(num_tubes, random_noise)
