# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_python_blender_code_that_creates_a_tubular_material_with_random_placement" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make python blender code that creates a tubular material with random placement.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule structure parameters
num_of_tubules = 20  # Number of tubules to create
noise_range = 0.1  # Noise range for positioning

def setup_cube_and_tubules(tubule_count, noise):
    # Create a base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    # Generate positions for the tubules
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

# Create the tubule structure
setup_cube_and_tubules(num_of_tubules, noise_range)
