# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_that_makes_a_cube_of_tubular_bioinspired_material__Think_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code that makes a cube of tubular bioinspired material. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubes = 16  # Chosen value for the number of tubules

def generate_tubes():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(num_tubes))
    tube_spacing = 2 / grid_dim
    initial_offset = -1 + tube_spacing / 2
    
    tube_positions = [(initial_offset + (i % grid_dim) * tube_spacing,
                       initial_offset + (i // grid_dim) * tube_spacing)
                      for i in range(num_tubes)]
    
    for pos_x, pos_y in tube_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        tube = bpy.context.object

        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tube

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        bpy.data.objects.remove(tube, do_unlink=True)

generate_tubes()
