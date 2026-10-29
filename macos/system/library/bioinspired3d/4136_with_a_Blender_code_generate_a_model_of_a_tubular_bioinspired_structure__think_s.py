# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_code_generate_a_model_of_a_tubular_bioinspired_structure__think_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender code generate a model of a tubular bioinspired structure. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubes = 16

def build_tubular_grid():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(num_tubes))
    tube_spacing = 2 / grid_dimension
    initial_offset = -1 + tube_spacing / 2
    
    tube_locations = [(initial_offset + (i % grid_dimension) * tube_spacing,
                       initial_offset + (i // grid_dimension) * tube_spacing)
                      for i in range(num_tubes)]
    
    for pos in tube_locations:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object

        bool_mod = main_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tube

        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        bpy.data.objects.remove(tube, do_unlink=True)

build_tubular_grid()
