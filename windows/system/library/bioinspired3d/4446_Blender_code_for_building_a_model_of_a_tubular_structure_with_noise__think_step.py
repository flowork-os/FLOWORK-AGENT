# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_for_building_a_model_of_a_tubular_structure_with_noise__think_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code for building a model of a tubular structure with noise. think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the number of tubules and noise level
tubule_total = 25  # Total number of tubules
noise_level = 0.06  # Maximum noise deviation

def create_structure(tubule_total, noise_level):
    # Start by adding a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(tubule_total))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    # Calculate positions for tubules
    positions = [(start_offset + (i % grid_size) * spacing,
                  start_offset + (i // grid_size) * spacing)
                 for i in range(tubule_total)]
    
    for pos in positions:
        x = pos[0] + random.uniform(-noise_level, noise_level)
        y = pos[1] + random.uniform(-noise_level, noise_level)
        add_tubule(cube, x, y)

def add_tubule(cube, x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
    tubule = bpy.context.object
    
    bool_modifier = cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
    bool_modifier.operation = 'DIFFERENCE'
    bool_modifier.object = tubule
    
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
    bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the function to create the structure
create_structure(tubule_total, noise_level)
