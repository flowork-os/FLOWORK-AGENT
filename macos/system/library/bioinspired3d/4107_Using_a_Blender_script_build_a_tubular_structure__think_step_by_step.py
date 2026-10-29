# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_Blender_script_build_a_tubular_structure__think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a Blender script build a tubular structure. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tube_count = 25  # Define the total number of tubes

def create_structure():
    """Creates a cube with embedded tubes."""
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(tube_count))
    distance = 2 / grid_size
    offset = -1 + distance / 2
    
    tube_positions = [(offset + (i % grid_size) * distance,
                       offset + (i // grid_size) * distance)
                      for i in range(tube_count)]
    
    for x, y in tube_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object

        bool_mod = main_cube.modifiers.new(name=f"CutTube_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tube

        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        bpy.data.objects.remove(tube, do_unlink=True)

create_structure()
