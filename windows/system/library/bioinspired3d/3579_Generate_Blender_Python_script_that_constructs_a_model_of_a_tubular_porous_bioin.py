# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_Python_script_that_constructs_a_model_of_a_tubular_porous_bioin" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender Python script that constructs a model of a tubular porous bioinspired structure with noisy tubule placement

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubule structure
number_of_tubules = 22
max_noise = 0.08

def create_tubule_structure(tubule_count, noise):
    # Initialize the cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_pos = -1 + spacing / 2
    initial_positions = [(start_pos + (i % grid_size) * spacing, start_pos + (i // grid_size) * spacing) for i in range(tubule_count)]
    final_positions = [(x + random.uniform(-noise, noise), y + random.uniform(-noise, noise)) for x, y in initial_positions]
    for x, y in final_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        bool_mod = cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

create_tubule_structure(number_of_tubules, max_noise)
