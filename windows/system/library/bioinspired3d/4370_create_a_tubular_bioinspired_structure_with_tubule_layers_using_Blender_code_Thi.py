# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_tubular_bioinspired_structure_with_tubule_layers_using_Blender_code_Thi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a tubular bioinspired structure with tubule layers using Blender code Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

number_of_tubules = 9  # Total number of tubules
layer_thickness_value = 0.07  # Thickness of layer around each tubule

def create_tubular_grid():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(number_of_tubules))
    spacing = 2 / grid_dim
    start_offset = -1 + spacing / 2
    
    positions = [(start_offset + (i % grid_dim) * spacing, 
                  start_offset + (i // grid_dim) * spacing) 
                 for i in range(number_of_tubules)]
    
    tubule_objects = []
    
    for x_pos, y_pos in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x_pos, y_pos, 0))
        inner_tubule = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness_value, depth=2, location=(x_pos, y_pos, 0))
        outer_tubule = bpy.context.object
        
        cube_modifier = main_cube.modifiers.new(name=f"Bool_Cube_{x_pos}_{y_pos}", type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        layer_modifier = inner_tubule.modifiers.new(name=f"Bool_Layer_{x_pos}_{y_pos}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)

        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        
        tubule_objects.append(inner_tubule)
    
    if tubule_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in tubule_objects:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = tubule_objects[0]
        bpy.ops.object.join()
        final_tubular_structure = bpy.context.object
        final_tubular_structure.name = "Final_Tubular_Structure"

create_tubular_grid()
