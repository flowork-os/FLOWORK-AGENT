# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_Blender_Python_script_that_generates_a_tubular_porous_bioinspired_structu" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create Blender Python script that generates a tubular porous bioinspired structure with noise. Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the parameters for the structure
num_tubules = 12
noise_level = 0.1

def create_tubules():
    # Create a base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    start = -1 + spacing / 2
    
    # Generate positions for the tubules
    positions = [(start + (i % grid_size) * spacing, start + (i // grid_size) * spacing) for i in range(num_tubules)]
    
    # Add noise to the positions
    for pos in positions:
        x, y = pos
        x += random.uniform(-noise_level, noise_level)
        y += random.uniform(-noise_level, noise_level)
        
        # Create a tubule at the noisy position
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        # Create and apply Boolean modifier
        bool_mod = cube.modifiers.new(name=f"BooleanOp_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Run the function to create tubules
create_tubules()
