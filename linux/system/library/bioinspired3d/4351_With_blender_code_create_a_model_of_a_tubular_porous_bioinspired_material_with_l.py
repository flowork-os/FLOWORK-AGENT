# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_code_create_a_model_of_a_tubular_porous_bioinspired_material_with_l" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender code create a model of a tubular porous bioinspired material with layers think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular structure
number_of_tubules = 9  # Number of tubules
layer_thickness = 0.07  # Thickness of the layer

def create_tubular_structure():
    # Start with a cube and create a grid of tubules
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(number_of_tubules))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    
    positions = [(offset + (i % grid_dim) * spacing, offset + (i // grid_dim) * spacing) for i in range(number_of_tubules)]
    
    shell_objects = []
    
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object
        
        bool_modifier = cube.modifiers.new(name=f"Inner_Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tube
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        bool_mod_layer = inner_tube.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        bool_mod_layer.operation = 'DIFFERENCE'
        bool_mod_layer.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=bool_mod_layer.name)
        
        bpy.data.objects.remove(outer_tube, do_unlink=True)
        shell_objects.append(inner_tube)
    
    if shell_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for shell in shell_objects:
            shell.select_set(True)
        bpy.context.view_layer.objects.active = shell_objects[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Final_Tubule_Shell"

# Create the tubular structure
create_tubular_structure()
