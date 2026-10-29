# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_construct_a_model_of_a_tubular_bioinspired_material__thin" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to construct a model of a tubular bioinspired material. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubes = 16

def build_tube_grid():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(num_tubes))
    tube_spacing = 2 / grid_dim
    offset = -1 + tube_spacing / 2
    
    tube_positions = [(offset + (i % grid_dim) * tube_spacing,
                       offset + (i // grid_dim) * tube_spacing)
                      for i in range(num_tubes)]
    
    for pos_x, pos_y in tube_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        tube = bpy.context.object
        
        bool_mod = base_cube.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tube
        
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        bpy.data.objects.remove(tube, do_unlink=True)

build_tube_grid()
