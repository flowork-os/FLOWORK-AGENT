# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_tubular_porous_structure_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a tubular porous structure using blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total number of tubes in the structure
tube_count = 25  # Define the total number of tubes


def create_structure():
    """Creates a cube with embedded tubes."""
    
    # Start by adding a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    # Determine the arrangement of tubes
    grid_size = math.ceil(math.sqrt(tube_count))
    distance = 2 / grid_size
    offset = -1 + distance / 2
    
    # Calculate the positions for the tubes
    tube_positions = [(offset + (i % grid_size) * distance,
                       offset + (i // grid_size) * distance)
                      for i in range(tube_count)]
    
    # Subtract each tube from the cube
    for x, y in tube_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object

        # Set up a Boolean modifier for subtraction
        bool_mod = main_cube.modifiers.new(name=f"CutTube_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tube

        # Apply the modifier to the cube
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        # Remove the tube after subtraction
        bpy.data.objects.remove(tube, do_unlink=True)

# Call the function to create the structure
create_structure()
