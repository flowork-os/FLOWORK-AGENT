# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_tubular_porous_bioinspired_material_with_jittered_placement_using_blend" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a tubular porous bioinspired material with jittered placement using blender code Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_tubules = 9  # Number of tubules
noise_level = 0.1  # Noise variation

def build_tubule_structure(total, noise):
    base_cube = bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(total))
    spacing = 2 / grid_dimension
    start_offset = -1 + spacing / 2
    
    tubule_positions = [(start_offset + (i % grid_dimension) * spacing, start_offset + (i // grid_dimension) * spacing) for i in range(total)]
    noisy_positions = [(x + random.uniform(-noise, noise), y + random.uniform(-noise, noise)) for x, y in tubule_positions]
    
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        boolean_mod = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

build_tubule_structure(total_tubules, noise_level)
