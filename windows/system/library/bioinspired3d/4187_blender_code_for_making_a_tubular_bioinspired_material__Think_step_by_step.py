# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_for_making_a_tubular_bioinspired_material__Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code for making a tubular bioinspired material. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tube_count = 15  # Selected value for the number of tubules

def construct_tubular_grid():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    grid_dimensions = math.ceil(math.sqrt(tube_count))
    gap = 2 / grid_dimensions
    initial_pos = -1 + gap / 2
    
    grid_positions = [(initial_pos + (i % grid_dimensions) * gap,
                        initial_pos + (i // grid_dimensions) * gap)
                       for i in range(tube_count)]
    
    for x_coord, y_coord in grid_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_coord, y_coord, 0))
        tube = bpy.context.object

        boolean_mod = cube.modifiers.new(name=f"Subtract_{x_coord}_{y_coord}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tube

        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

        bpy.data.objects.remove(tube, do_unlink=True)

construct_tubular_grid()
