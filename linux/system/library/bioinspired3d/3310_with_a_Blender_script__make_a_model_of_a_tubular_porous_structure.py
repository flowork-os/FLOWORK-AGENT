# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_script__make_a_model_of_a_tubular_porous_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender script, make a model of a tubular porous structure

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the total number of tubes
num_tubes = 12

def build_structure():
    # This function builds a cube with subtracted tubules.
    # 1. Create the cube.
    # 2. Calculate tubule positions in a grid.
    # 3. Subtract tubules using Boolean modifiers.
    
    # Create a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    # Calculate grid size
    grid_size = math.ceil(math.sqrt(num_tubes))
    spacing = 2 / grid_size
    start_pos = -1 + spacing / 2
    
    # Generate positions for tubules
    positions = [(start_pos + (i % grid_size) * spacing,
                   start_pos + (i // grid_size) * spacing)
                  for i in range(num_tubes)]
    
    # Subtract each tubule from the cube
    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        bool_mod = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the structure building function
build_structure()
