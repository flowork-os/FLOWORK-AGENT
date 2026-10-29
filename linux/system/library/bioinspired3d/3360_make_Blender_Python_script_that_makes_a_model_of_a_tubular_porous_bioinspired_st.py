# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_Blender_Python_script_that_makes_a_model_of_a_tubular_porous_bioinspired_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make Blender Python script that makes a model of a tubular porous bioinspired structure

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Number of tubules to create
tubule_total = 12  # Total number of tubules


def create_tubule_structure(tubule_total):
    # Function to create a structure with tubules subtracted from a cube.
    # 1. Create a base cube.
    # 2. Arrange tubules in a grid pattern.
    # 3. Subtract each tubule from the cube using Boolean modifiers.
    
    # Create the base cube object
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    # Get grid size for tubules
    grid_count = math.ceil(math.sqrt(tubule_total))
    spacing = 2 / grid_count
    offset = -1 + spacing / 2
    
    # Calculate positions for each tubule
    positions = [(offset + (i % grid_count) * spacing,
                  offset + (i // grid_count) * spacing)
                 for i in range(tubule_total)]
    
    # Create and subtract each tubule
    for x_pos, y_pos in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_pos, y_pos, 0))
        tubule = bpy.context.object

        # Create Boolean modifier for the subtraction
        boolean_mod = cube.modifiers.new(name=f"Subtract_{x_pos}_{y_pos}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tubule

        # Apply the modifier to the cube
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

        # Remove the tubule object
        bpy.data.objects.remove(tubule, do_unlink=True)

# Call the function to create the structure
create_tubule_structure(tubule_total)
