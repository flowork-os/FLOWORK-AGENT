# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_Python_script_create_a_tubular_porous_material_with_jittered_pl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender Python script create a tubular porous material with jittered placement Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tube structure
total_tubules = 20  # Number of tubes
jitter_amount = 0.05  # Amount of noise for placement

def create_tube_structure(count=20, jitter=0.05):
    # Step 1: Generate a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    # Step 2: Calculate positions for the tubes
    tube_positions = [(offset + (i % grid_size) * spacing, 
                        offset + (i // grid_size) * spacing) 
                       for i in range(count)]

    # Step 3: Add noise to the positions
    perturbed_positions = [(x + random.uniform(-jitter, jitter), 
                            y + random.uniform(-jitter, jitter)) for x, y in tube_positions]

    # Step 4: Subtract cylinders from the cube
    for x, y in perturbed_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object

        # Boolean operation to subtract the tube
        boolean_mod = cube.modifiers.new(name='SubtractTube', type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tube

        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

        bpy.data.objects.remove(tube, do_unlink=True)

# Execute tube creation
create_tube_structure(total_tubules, jitter_amount)
