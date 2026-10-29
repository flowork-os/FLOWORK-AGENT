# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_for_creating_a_model_of_a_tubular_porous_material_Think_step_by_ste" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code for creating a model of a tubular porous material Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tube_quantity = 16  # Total number of tubes

def build_tubes():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(tube_quantity))
    spacing_distance = 2 / grid_dimension
    offset_start = -1 + spacing_distance / 2
    
    tube_positions = [
        (offset_start + (i % grid_dimension) * spacing_distance, 
         offset_start + (i // grid_dimension) * spacing_distance)
        for i in range(tube_quantity)
    ]
    
    for pos_x, pos_y in tube_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        tube = bpy.context.object
        
        boolean_modifier = base_cube.modifiers.new(name=f"Subtraction_{pos_x}_{pos_y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tube
        
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(tube, do_unlink=True)

build_tubes()
