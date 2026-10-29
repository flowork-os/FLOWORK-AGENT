# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_script_construct_a_tubular_material_with_noise__Think_step_by_ste" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender script construct a tubular material with noise. Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the parameters for the tubular structure
count_of_tubules = 12
noise_amplitude = 0.06

# Function to create the tubular structure
def build_tubular_structure(tubule_count, noise):
    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(tubule_count))
    interval = 2 / grid_dimension
    offset = -1 + interval / 2
    
    # Calculate positions for tubules
    position_list = [(offset + (i % grid_dimension) * interval, 
                      offset + (i // grid_dimension) * interval) 
                     for i in range(tubule_count)]
    
    # Add noise to the positions
    noisy_positions = [(x + random.uniform(-noise, noise), 
                        y + random.uniform(-noise, noise)) for x, y in position_list]
    
    for x, y in noisy_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        bool_mod = cube_base.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the creation of the tubular structure
build_tubular_structure(count_of_tubules, noise_amplitude)
