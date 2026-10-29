# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_tubular_porous_structure_with_noise_using_blender_python_code_think_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a tubular porous structure with noise using blender python code think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the model
num_tubules = 18
noise_level = 0.09

# Function to create and modify the 3D structure
def build_tubule_structure(tubule_count, noise_variance):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_dim
    initial_offset = -1 + spacing / 2
    positions = [(initial_offset + (i % grid_dim) * spacing, 
                  initial_offset + (i // grid_dim) * spacing) 
                 for i in range(tubule_count)]
    disturbed_positions = [(x + random.uniform(-noise_variance, noise_variance), 
                            y + random.uniform(-noise_variance, noise_variance)) for x, y in positions]
    for x, y in disturbed_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        cylinder = bpy.context.object
        bool_mod = main_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = cylinder
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(cylinder, do_unlink=True)

# Execute the structure creation
build_tubule_structure(num_tubules, noise_level)
