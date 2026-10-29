# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_tubular_porous_bioinspired_material_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a tubular porous bioinspired material in Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular formation
num_tubules = 16  # Number of tubules in the structure


def generate_tubules():
    # Function to create a grid of tubules within a cube.
    # Steps:
    # 1. Generate a cube.
    # 2. Arrange tubules in a grid layout.
    # 3. Subtract tubules from the cube using Boolean modifiers.
    
    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine the grid configuration for tubules
    grid_dimension = math.ceil(math.sqrt(num_tubules))
    separation = 2 / grid_dimension
    initial_offset = -1 + separation / 2
    
    # Calculate positions for each tubule
    coordinates = [(initial_offset + (i % grid_dimension) * separation,
                    initial_offset + (i // grid_dimension) * separation)
                   for i in range(num_tubules)]
    
    # Loop through calculated positions to create and subtract tubules
    for x_pos, y_pos in coordinates:
        # Add a cylinder at the specified position
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_pos, y_pos, 0))
        tubule_cylinder = bpy.context.object

        # Create a Boolean modifier for subtraction
        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{x_pos}_{y_pos}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule_cylinder

        # Apply the modifier to the cube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        # Delete the tubule after subtraction
        bpy.data.objects.remove(tubule_cylinder, do_unlink=True)

# Execute tubule generation
generate_tubules()
