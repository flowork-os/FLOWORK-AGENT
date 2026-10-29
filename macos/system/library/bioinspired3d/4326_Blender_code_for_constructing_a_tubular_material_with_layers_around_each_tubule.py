# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_for_constructing_a_tubular_material_with_layers_around_each_tubule" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code for constructing a tubular material with layers around each tubule think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 22  # Number of tubules
layer_thickness = 0.06  # Thickness of the layer around each tubule

def create_tubular_grid():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    positions = [
        (start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing)
        for i in range(num_tubules)
    ]
    
    processed_tubules = []
    
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        
        cube_modifier = base_cube.modifiers.new(name=f'Cube_Bool_{x}_{y}', type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        inner_modifier = inner_tubule.modifiers.new(name=f'Inner_Bool_{x}_{y}', type='BOOLEAN')
        inner_modifier.operation = 'DIFFERENCE'
        inner_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=inner_modifier.name)

        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        
        processed_tubules.append(inner_tubule)
    
    if processed_tubules:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in processed_tubules:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = processed_tubules[0]
        bpy.ops.object.join()
        final_tubular_structure = bpy.context.object
        final_tubular_structure.name = 'Final_Tubular_Grid'

create_tubular_grid()
