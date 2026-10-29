# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_cube_of_tubular_material_using_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a cube of tubular material using a blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set the number of tubes in the structure
tube_quantity = 16  # Total number of tubes


def build_tubes():
    # Function to create a cube and subtract a grid of tubes from it.
    # Steps:
    # 1. Create a base cube.
    # 2. Calculate positions for the tubes.
    # 3. Subtract each tube using Boolean modifiers.
    
    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid size for tube placement
    grid_dimension = math.ceil(math.sqrt(tube_quantity))
    spacing_distance = 2 / grid_dimension
    offset_start = -1 + spacing_distance / 2
    
    # Calculate positions for the tubes
    tube_positions = [
        (offset_start + (i % grid_dimension) * spacing_distance, 
         offset_start + (i // grid_dimension) * spacing_distance)
        for i in range(tube_quantity)
    ]
    
    # Create tubes and apply Boolean modifiers
    for pos_x, pos_y in tube_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        tube = bpy.context.object
        
        boolean_modifier = base_cube.modifiers.new(name=f"Subtraction_{pos_x}_{pos_y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tube
        
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(tube, do_unlink=True)

# Execute tube building function
build_tubes()
