# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_Blender_code__generate_a_model_of_a_cube_of_tubular_material_with_tubule" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a Blender code, generate a model of a cube of tubular material with tubule layers. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_tubules = 12  # Number of tubules
layer_width = 0.04  # Thickness of the layer around each tubule

def create_tubular_structure():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    
    positions = [(offset + (i % grid_dim) * spacing, 
                   offset + (i // grid_dim) * spacing) 
                  for i in range(total_tubules)]
    
    processed_tubules = []
    
    for position_x, position_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(position_x, position_y, 0))
        inner_tubule = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(position_x, position_y, 0))
        outer_tubule = bpy.context.object
        
        cube_modifier = main_cube.modifiers.new(name=f"Cube_Bool_{position_x}_{position_y}", type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        shell_modifier = inner_tubule.modifiers.new(name=f"Shell_Bool_{position_x}_{position_y}", type='BOOLEAN')
        shell_modifier.operation = 'DIFFERENCE'
        shell_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=shell_modifier.name)

        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        
        processed_tubules.append(inner_tubule)
    
    if processed_tubules:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in processed_tubules:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = processed_tubules[0]
        bpy.ops.object.join()
        final_tubule_shell = bpy.context.object
        final_tubule_shell.name = "Final_Tubule_Shell"

create_tubular_structure()
