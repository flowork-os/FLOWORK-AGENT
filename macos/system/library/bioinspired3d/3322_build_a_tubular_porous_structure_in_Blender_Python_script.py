# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_tubular_porous_structure_in_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a tubular porous structure in Blender Python script

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the number of tubes
tubes_count = 12

# Function to generate the 3D structure

def generate_structure():
    # Create a cube and subtract cylindrical tubes from it
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object

    # Determine grid size and spacing
    grid_size = math.ceil(math.sqrt(tubes_count))
    spacing = 2 / grid_size
    start = -1 + spacing / 2

    # Generate positions for each tube
    for i in range(tubes_count):
        pos_x = start + (i % grid_size) * spacing
        pos_y = start + (i // grid_size) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        tube = bpy.context.object

        # Create and apply Boolean modifier
        bool_modifier = main_cube.modifiers.new(name=f"Subtract_{i}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tube

        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        # Remove the tube after applying the modifier
        bpy.data.objects.remove(tube, do_unlink=True)

# Execute function to create the structure
generate_structure()
