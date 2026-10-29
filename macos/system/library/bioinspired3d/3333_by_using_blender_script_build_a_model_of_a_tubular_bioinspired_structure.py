# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_script_build_a_model_of_a_tubular_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender script build a model of a tubular bioinspired structure

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the number of tubes
tube_count = 20

def generate_tube_structure():
    # Function to generate a cube with multiple tube cutouts.
    # Steps involved:
    # 1. Create a cube.
    # 2. Determine tube positions in a grid.
    # 3. Subtract the tubes using Boolean modifiers.
    
    # Create a cube base
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    # Calculate grid parameters
    grid_dim = math.ceil(math.sqrt(tube_count))
    tube_spacing = 2 / grid_dim
    initial_offset = -1 + tube_spacing / 2
    
    # Calculate positions for the tubes
    tube_positions = [(initial_offset + (i % grid_dim) * tube_spacing,
                        initial_offset + (i // grid_dim) * tube_spacing)
                       for i in range(tube_count)]
    
    # Create tubes and apply Boolean operations
    for pos in tube_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos[0], pos[1], 0))
        tube = bpy.context.object

        bool_modifier = main_cube.modifiers.new(name=f"SubtractTube_{pos[0]}_{pos[1]}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tube

        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        bpy.data.objects.remove(tube, do_unlink=True)

# Call the function to generate the structure
generate_tube_structure()
