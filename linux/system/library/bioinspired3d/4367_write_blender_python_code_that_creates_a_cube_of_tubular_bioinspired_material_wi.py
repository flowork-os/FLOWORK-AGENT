# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_python_code_that_creates_a_cube_of_tubular_bioinspired_material_wi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender python code that creates a cube of tubular bioinspired material with layers around each tubule. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tubule_quantity = 25  # Number of tubules
shell_thickness = 0.03  # Thickness of the shell around each tubule

def construct_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(tubule_quantity))
    spacing = 2 / grid_dim
    start = -1 + spacing / 2
    
    tubule_positions = [(start + (i % grid_dim) * spacing, 
                         start + (i // grid_dim) * spacing) 
                        for i in range(tubule_quantity)]
    
    created_tubules = []
    
    for pos_x, pos_y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_tubule = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - shell_thickness, depth=2, location=(pos_x, pos_y, 0))
        outer_tubule = bpy.context.object
        
        bool_modifier = cube_base.modifiers.new(name=f"Inner_Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        shell_modifier = inner_tubule.modifiers.new(name=f"Shell_Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        shell_modifier.operation = 'DIFFERENCE'
        shell_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=shell_modifier.name)

        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        
        created_tubules.append(inner_tubule)
    
    if created_tubules:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in created_tubules:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = created_tubules[0]
        bpy.ops.object.join()
        combined_shell = bpy.context.object
        combined_shell.name = "Combined_Tubule_Shell"

construct_tubules()
