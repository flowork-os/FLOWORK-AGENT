# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_that_builds_a_model_of_a_tubular_porous_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code that builds a model of a tubular porous structure

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Number of tubes to create
num_tubes = 16


def build_tubular_structure():
    # Function to construct the cube with tubules
    # 1. Initialize a cube.
    # 2. Position tubules in a grid.
    # 3. Apply Boolean operations to carve out tubules from the cube.
    
    # Add the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid layout for tubules
    grid_dim = math.ceil(math.sqrt(num_tubes))
    tube_spacing = 2 / grid_dim
    initial_offset = -1 + tube_spacing / 2
    
    # Calculate tubule positions
    tubule_positions = [(initial_offset + (i % grid_dim) * tube_spacing, 
                          initial_offset + (i // grid_dim) * tube_spacing) 
                         for i in range(num_tubes)]
    
    # Create and subtract each tubule
    for pos_x, pos_y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        current_tubule = bpy.context.object

        # Set up Boolean modifier
        bool_modifier = base_cube.modifiers.new(name=f"Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule

        # Apply the Boolean modifier to the cube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        # Cleanup: remove the tubule
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Execute the structure creation
build_tubular_structure()
