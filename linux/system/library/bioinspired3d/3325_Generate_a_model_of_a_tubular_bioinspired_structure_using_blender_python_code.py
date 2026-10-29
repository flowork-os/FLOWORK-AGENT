# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_tubular_bioinspired_structure_using_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a tubular bioinspired structure using blender python code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Number of tubular structures to create
num_tubules = 16  # Total count of tubules

def generate_tubules():
    # Function to create a cube with a grid of tubules
    # 1. Initialize a cube.
    # 2. Position tubules in a grid.
    # 3. Apply Boolean modifiers to remove tubules.
    
    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid dimensions for tubules
    grid_dim = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    
    # Calculate tubule positions
    tubule_positions = [
        (offset + (i % grid_dim) * spacing, offset + (i // grid_dim) * spacing)
        for i in range(num_tubules)
    ]
    
    # Create and subtract tubules from the cube
    for x, y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        current_tubule = bpy.context.object
        
        # Set up Boolean modifier for subtraction
        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule
        
        # Apply the Boolean operation
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Clean up by removing the tubule
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Execute the tubule generation
generate_tubules()
