# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_a_tubular_porous_structure_using_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of a tubular porous structure using a Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Number of tubes in the grid
num_tubes = 16  # Chosen value for the number of tubules


def generate_tubes():
    # Function to create a cubic structure with cylindrical tubules
    # Steps:
    # 1. Create a base cube.
    # 2. Position tubules in a grid layout.
    # 3. Subtract tubules using Boolean operations.
    
    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid size for positioning
    grid_dim = math.ceil(math.sqrt(num_tubes))
    tube_spacing = 2 / grid_dim
    initial_offset = -1 + tube_spacing / 2
    
    # Calculate positions for each tube
    tube_positions = [(initial_offset + (i % grid_dim) * tube_spacing,
                       initial_offset + (i // grid_dim) * tube_spacing)
                      for i in range(num_tubes)]
    
    # Create and subtract each tube from the cube
    for pos_x, pos_y in tube_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        tube = bpy.context.object

        # Set up Boolean modifier for subtraction
        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tube

        # Apply the Boolean operation
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        # Delete the tube object after operation
        bpy.data.objects.remove(tube, do_unlink=True)

# Execute the tubule generation
generate_tubes()
