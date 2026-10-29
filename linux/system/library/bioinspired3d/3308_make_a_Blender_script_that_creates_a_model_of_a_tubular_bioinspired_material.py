# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_Blender_script_that_creates_a_model_of_a_tubular_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a Blender script that creates a model of a tubular bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the number of tubules
total_tubules = 20

def generate_tubules():
    # Function to create a cube and subtract tubules from it.
    # 1. Cube is created.
    # 2. Tubules are positioned in a grid.
    # 3. Boolean operations subtract the tubules.
    
    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Calculate the grid arrangement
    grid_count = math.ceil(math.sqrt(total_tubules))
    distance = 2 / grid_count
    offset = -1 + distance / 2
    
    # Determine positions for each tubule
    positions = []
    for i in range(total_tubules):
        x = offset + (i % grid_count) * distance
        y = offset + (i // grid_count) * distance
        positions.append((x, y))
    
    # Subtract tubules from the cube
    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object
        boolean_modifier = base_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(tube, do_unlink=True)

# Execute the tubule generation
generate_tubules()
