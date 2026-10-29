# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_python_blender_code_make_a_model_of_a_tubular_porous_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using python blender code make a model of a tubular porous bioinspired structure with jittered placement Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_of_tubules = 20  # Number of tubules to create
noise_range = 0.1  # Noise range for positioning

def setup_cube_and_tubules(tubule_count, noise):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    tubule_positions = [(offset + (i % grid_size) * spacing, 
                         offset + (i // grid_size) * spacing) 
                        for i in range(tubule_count)]
    
    for position in tubule_positions:
        x = position[0] + random.uniform(-noise, noise)
        y = position[1] + random.uniform(-noise, noise)
        add_tubule(base_cube, x, y)

def add_tubule(cube, x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
    tubule = bpy.context.object
    
    boolean_modifier = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
    boolean_modifier.operation = 'DIFFERENCE'
    boolean_modifier.object = tubule
    
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
    bpy.data.objects.remove(tubule, do_unlink=True)

setup_cube_and_tubules(num_of_tubules, noise_range)
