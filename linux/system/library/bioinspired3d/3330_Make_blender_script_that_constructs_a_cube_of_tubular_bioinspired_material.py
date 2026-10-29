# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_blender_script_that_constructs_a_cube_of_tubular_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make blender script that constructs a cube of tubular bioinspired material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Number of cylindrical features in the model
num_cylinders = 16

def build_structure():
    # Function to create a cube with cylindrical cutouts.
    # Steps:
    # 1. Add a cube.
    # 2. Calculate positions for cylinders in a grid.
    # 3. Subtract cylinders using Boolean operations.
    
    # Initialize the cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid size and spacing
    grid_dimension = math.ceil(math.sqrt(num_cylinders))
    spacing_distance = 2 / grid_dimension
    offset_start = -1 + spacing_distance / 2
    
    # Calculate cylinder positions
    cylinder_positions = [(offset_start + (i % grid_dimension) * spacing_distance,
                           offset_start + (i // grid_dimension) * spacing_distance)
                          for i in range(num_cylinders)]
    
    # Create cylinders and perform Boolean subtraction
    for pos in cylinder_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos[0], pos[1], 0))
        cylinder = bpy.context.object

        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{pos[0]}_{pos[1]}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = cylinder

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        bpy.data.objects.remove(cylinder, do_unlink=True)

# Execute the structure creation
build_structure()
