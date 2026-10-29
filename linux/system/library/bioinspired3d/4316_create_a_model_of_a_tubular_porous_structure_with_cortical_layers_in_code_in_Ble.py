# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_a_tubular_porous_structure_with_cortical_layers_in_code_in_Ble" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of a tubular porous structure with cortical layers in code in Blender Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 22  # Total number of tubules
layer_thickness = 0.07  # Thickness of layer surrounding each tubule

def construct_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset_start = -1 + spacing / 2
    
    positions = [(offset_start + (i % grid_size) * spacing, 
                   offset_start + (i // grid_size) * spacing) 
                  for i in range(num_tubules)]
    
    created_shells = []
    
    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_tube = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(pos_x, pos_y, 0))
        outer_tube = bpy.context.object
        
        cube_bool = base_cube.modifiers.new(name=f"Cube_Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        cube_bool.operation = 'DIFFERENCE'
        cube_bool.object = inner_tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=cube_bool.name)
        
        inner_bool = inner_tube.modifiers.new(name=f"Inner_Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        inner_bool.operation = 'DIFFERENCE'
        inner_bool.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=inner_bool.name)

        bpy.data.objects.remove(outer_tube, do_unlink=True)

        created_shells.append(inner_tube)
        
    if created_shells:
        bpy.ops.object.select_all(action='DESELECT')
        for shell in created_shells:
            shell.select_set(True)
        bpy.context.view_layer.objects.active = created_shells[0]
        bpy.ops.object.join()
        final_tubular_structure = bpy.context.object
        final_tubular_structure.name = "Merged_Tubular_Structure"

construct_tubules()
