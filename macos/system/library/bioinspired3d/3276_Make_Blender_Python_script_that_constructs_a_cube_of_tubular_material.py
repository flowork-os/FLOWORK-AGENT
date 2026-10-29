# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_Blender_Python_script_that_constructs_a_cube_of_tubular_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make Blender Python script that constructs a cube of tubular material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Number of cylindrical protrusions in the design
num_protrusions = 16  # Set the total count of protrusions


def generate_protrusions():
    # Function to create a cube with cylindrical protrusions.
    # Steps:
    # 1. Form a base cube.
    # 2. Position cylinders in a grid layout.
    # 3. Apply Boolean operations to remove cylinders from the cube.
    
    # Add a cube as the base shape
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine the grid layout for the cylinders
    grid_dimension = math.ceil(math.sqrt(num_protrusions))
    cylinder_spacing = 2 / grid_dimension
    initial_offset = -1 + cylinder_spacing / 2
    
    # Calculate positions for the cylinders within the grid
    cylinder_positions = [(initial_offset + (i % grid_dimension) * cylinder_spacing,
                           initial_offset + (i // grid_dimension) * cylinder_spacing)
                          for i in range(num_protrusions)]
    
    # Loop through each position to subtract cylinders from the cube
    for pos_x, pos_y in cylinder_positions:
        # Add a cylinder (protrusion) at the specified position
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        cylinder = bpy.context.object

        # Create a Boolean modifier to subtract the cylinder from the cube
        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = cylinder

        # Set the cube as the active object to apply the modifier
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        # Delete the cylinder after performing the subtraction
        bpy.data.objects.remove(cylinder, do_unlink=True)

# Execute the creation of protrusions
generate_protrusions()
