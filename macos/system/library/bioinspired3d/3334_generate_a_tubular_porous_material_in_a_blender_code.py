# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_tubular_porous_material_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a tubular porous material in a blender code

import bpy
import math

# Clear the existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total number of tubes
total_tubules = 22

def create_tubular_structure():
    # This function builds a cube with cylindrical cutouts.
    # Steps:
    # 1. Generate a cube.
    # 2. Determine positions for the cylinders.
    # 3. Apply Boolean modifiers to subtract cylinders from the cube.
    
    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Calculate grid size and spacing
    grid_size = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    # Calculate positions for the cylinders
    cylinder_positions = [(start_offset + (i % grid_size) * spacing,
                           start_offset + (i // grid_size) * spacing)
                          for i in range(total_tubules)]
    
    # Create cylinders and apply Boolean modifiers
    for position in cylinder_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(position[0], position[1], 0))
        cylinder = bpy.context.object

        boolean_modifier = base_cube.modifiers.new(name=f"Cutout_{position[0]}_{position[1]}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = cylinder

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)

        bpy.data.objects.remove(cylinder, do_unlink=True)

# Execute the function to create the structure
create_tubular_structure()
