# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_python_code_build_a_tubular_porous_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender python code build a tubular porous structure

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the count of tubules
number_of_tubules = 12  # Chosen number of tubules


def make_tubules():
    # Function to build a cube and subtract tubules
    # Steps:
    # 1. Create a cube.
    # 2. Arrange tubules in a grid format.
    # 3. Subtract tubules from the cube using Boolean modifiers.
    
    # Add a cube as the base
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid layout
    grid_dim = math.ceil(math.sqrt(number_of_tubules))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    
    # Calculate positions for each tubule
    positions = [(offset + (i % grid_dim) * spacing,
                   offset + (i // grid_dim) * spacing)
                  for i in range(number_of_tubules)]
    
    # Create and subtract each tubule
    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        tubule = bpy.context.object

        # Setup Boolean modifier
        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule

        # Apply the Boolean modifier
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        # Remove the tubule object
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the tubule creation
make_tubules()
