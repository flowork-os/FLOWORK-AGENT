# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_Python_script__build_a_model_of_a_tubular_porous_bioinspired_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender Python script, build a model of a tubular porous bioinspired structure

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total number of cylindrical elements in the structure
number_of_tubules = 16

def generate_tubular_structure():
    # Constructs a cube with a grid of cylindrical tubules.
    # Steps:
    # 1. Create a cube.
    # 2. Position tubules in a grid.
    # 3. Use Boolean modifiers for subtraction.
    
    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid size for positioning tubules
    grid_dimension = math.ceil(math.sqrt(number_of_tubules))
    spacing_between_tubules = 2 / grid_dimension
    initial_offset = -1 + spacing_between_tubules / 2
    
    # Calculate the positions for the tubules
    tubule_positions = [(initial_offset + (i % grid_dimension) * spacing_between_tubules, 
                         initial_offset + (i // grid_dimension) * spacing_between_tubules) 
                        for i in range(number_of_tubules)]
    
    # Subtract each tubule from the cube
    for pos_x, pos_y in tubule_positions:
        # Add a cylinder at the specified position
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        current_tubule = bpy.context.object

        # Create a Boolean modifier for subtraction
        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule

        # Apply the Boolean modifier
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        # Delete the tubule after applying the modifier
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Execute the creation of the tubular structure
generate_tubular_structure()
