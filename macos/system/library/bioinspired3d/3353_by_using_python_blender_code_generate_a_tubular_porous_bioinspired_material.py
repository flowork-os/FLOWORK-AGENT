# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_python_blender_code_generate_a_tubular_porous_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using python blender code generate a tubular porous bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total number of cylindrical structures
tubule_count = 25  # Defined number of tubules


def create_cylinders():
    # Main function to create a cube and subtract cylindrical tubules
    # Procedure:
    # 1. Generate a cube.
    # 2. Calculate positions for tubules in a grid.
    # 3. Apply Boolean modifiers to cut out tubules.
    
    # Create a cube as the base shape
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    
    # Calculate the grid layout
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    # Generate coordinates for tubules
    coords = [(offset + (i % grid_size) * spacing,
                offset + (i // grid_size) * spacing)
               for i in range(tubule_count)]
    
    # Loop through coordinates to create and subtract tubules
    for x_pos, y_pos in coords:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_pos, y_pos, 0))
        cylinder = bpy.context.object

        # Create a Boolean modifier for the subtraction
        bool_mod = cube_base.modifiers.new(name=f"Cutout_{x_pos}_{y_pos}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = cylinder

        # Apply the modifier to the cube
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        # Remove the cylinder after the operation
        bpy.data.objects.remove(cylinder, do_unlink=True)

# Call the function to create the tubular structure
create_cylinders()
