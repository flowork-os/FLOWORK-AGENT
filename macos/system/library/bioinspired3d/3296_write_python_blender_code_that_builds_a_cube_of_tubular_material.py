# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_python_blender_code_that_builds_a_cube_of_tubular_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write python blender code that builds a cube of tubular material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Number of tubes in the design
num_tubes = 16

def build_tubular_structure():
    # This function constructs a cube with a grid of cylindrical tubules.
    # Steps:
    # 1. Create a cube as the base.
    # 2. Arrange tubules in a defined grid.
    # 3. Subtract the tubules using Boolean modifiers.
    
    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid dimensions for the tubules
    grid_dim = math.ceil(math.sqrt(num_tubes))
    spacing = 2 / grid_dim
    initial_offset = -1 + spacing / 2
    
    # Calculate positions for each tubule
    tubule_positions = [(initial_offset + (i % grid_dim) * spacing,
                         initial_offset + (i // grid_dim) * spacing)
                        for i in range(num_tubes)]
    
    # Create and subtract each tubule from the cube
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

        # Clean up by removing the tubule object
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Execute the structure creation
build_tubular_structure()
