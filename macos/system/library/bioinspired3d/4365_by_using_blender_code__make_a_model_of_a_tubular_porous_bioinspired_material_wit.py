# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_code__make_a_model_of_a_tubular_porous_bioinspired_material_wit" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender code, make a model of a tubular porous bioinspired material with tubule layers. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 9  # Total number of tubules
layer_thickness = 0.07  # Thickness of layer surrounding each tubule

def construct_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    positions = [(start_offset + (i % grid_size) * spacing,
                  start_offset + (i // grid_size) * spacing)
                 for i in range(num_tubules)]
    
    processed_layers = []
    
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        
        cube_modifier = cube.modifiers.new(name=f'bool_{x}_{y}', type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        shell_modifier = inner_tubule.modifiers.new(name=f'shell_{x}_{y}', type='BOOLEAN')
        shell_modifier.operation = 'DIFFERENCE'
        shell_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=shell_modifier.name)

        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        
        processed_layers.append(inner_tubule)
    
    if processed_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in processed_layers:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = processed_layers[0]
        bpy.ops.object.join()
        final_object = bpy.context.object
        final_object.name = 'Layer_Shell'

construct_tubules()
