# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_builds_a_model_of_a_tubular_material_with_layers_around_each_t" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that builds a model of a tubular material with layers around each tubule. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 16  # Total number of tubules
layer_width = 0.05  # Thickness of layer surrounding each tubule

def create_tubular_structure():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    tubule_positions = [
        (offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing)
        for i in range(num_tubules)
    ]
    
    shell_objects = []
    
    for x, y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        
        bool_mod_cube = main_cube.modifiers.new(name=f'Bool_Cube_{x}_{y}', type='BOOLEAN')
        bool_mod_cube.operation = 'DIFFERENCE'
        bool_mod_cube.object = inner_tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod_cube.name)
        
        bool_mod_shell = inner_tubule.modifiers.new(name=f'Bool_Shell_{x}_{y}', type='BOOLEAN')
        bool_mod_shell.operation = 'DIFFERENCE'
        bool_mod_shell.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=bool_mod_shell.name)

        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        
        shell_objects.append(inner_tubule)
    
    if shell_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in shell_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = shell_objects[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = 'Final_Tubular_Shell'

create_tubular_structure()
