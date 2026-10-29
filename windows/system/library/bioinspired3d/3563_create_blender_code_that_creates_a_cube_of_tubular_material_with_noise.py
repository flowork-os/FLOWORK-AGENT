# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_blender_code_that_creates_a_cube_of_tubular_material_with_noise" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create blender code that creates a cube of tubular material with noise.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the creation of tubules
num_tubules = 25
noise_variance = 0.06

def setup_tubule_structure():
    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    # Create positions for the tubules
    positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(num_tubules)]
    
    # Apply noise to the positions
    for pos in positions:
        x, y = pos
        x_noise = random.uniform(-noise_variance, noise_variance)
        y_noise = random.uniform(-noise_variance, noise_variance)
        
        # Create a cylinder at the noisy position
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x + x_noise, y + y_noise, 0))
        tubule_cylinder = bpy.context.object
        
        # Create a Boolean modifier to subtract the tubule
        bool_modifier = main_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule_cylinder
        
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule_cylinder, do_unlink=True)

# Execute the setup
setup_tubule_structure()
