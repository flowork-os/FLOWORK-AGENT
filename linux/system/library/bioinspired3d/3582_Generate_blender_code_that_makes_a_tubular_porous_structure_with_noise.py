# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_code_that_makes_a_tubular_porous_structure_with_noise" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender code that makes a tubular porous structure with noise.

import bpy
import math
import random

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular object
num_tubes = 12  # Number of tubes to generate
random_noise = 0.1  # Noise level for tube placement

def create_structure(tube_count, noise_level):
    # Create a cube to serve as a base for the structure
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    
    # Determine the grid size and spacing
    grid_dimension = math.ceil(math.sqrt(tube_count))
    tube_spacing = 2 / grid_dimension
    offset = -1 + tube_spacing / 2
    
    # Generate positions for each tube
    positions = [(offset + (i % grid_dimension) * tube_spacing,
                  offset + (i // grid_dimension) * tube_spacing)
                 for i in range(tube_count)]
    
    # Add noise to the positions
    noisy_positions = [(x + random.uniform(-noise_level, noise_level),
                        y + random.uniform(-noise_level, noise_level)) for x, y in positions]
    
    # Subtract each tube from the cube
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

# Execute the creation of the structure
create_structure(num_tubes, random_noise)
