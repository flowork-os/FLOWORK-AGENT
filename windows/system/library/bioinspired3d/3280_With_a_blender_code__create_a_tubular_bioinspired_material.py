# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_blender_code__create_a_tubular_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a blender code, create a tubular bioinspired material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total count of tubular structures
count_tubules = 18  # Define the number of tubules

def create_tube_grid():
    """Creates a cube with a grid of tubes removed."""
    
    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    # Calculate grid layout
    grid_size = math.ceil(math.sqrt(count_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    # Positioning for each tube
    tube_positions = [(start_offset + (i % grid_size) * spacing,
                       start_offset + (i // grid_size) * spacing)
                      for i in range(count_tubules)]
    
    # Subtract tubes from the cube
    for x, y in tube_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object
        bool_mod = main_cube.modifiers.new(name=f"RemoveTube_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tube
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tube, do_unlink=True)

# Generate the tube grid
create_tube_grid()
