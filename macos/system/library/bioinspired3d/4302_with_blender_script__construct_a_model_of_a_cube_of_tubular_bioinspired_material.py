# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_script__construct_a_model_of_a_cube_of_tubular_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender script, construct a model of a cube of tubular bioinspired material with layers around each tubule Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 16  # Total count of tubules
layer_width = 0.05  # Thickness of the layer surrounding each tubule

def generate_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(num_tubules))
    gap = 2 / grid_dimension
    offset = -1 + gap / 2
    
    positions = [(offset + (i % grid_dimension) * gap, 
                   offset + (i // grid_dimension) * gap) 
                  for i in range(num_tubules)]
    
    tubular_layers = []
    
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object
        
        boolean_modifier = base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = inner_tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        
        outer_boolean = inner_tube.modifiers.new(name=f"Outer_Bool_{x}_{y}", type='BOOLEAN')
        outer_boolean.operation = 'DIFFERENCE'
        outer_boolean.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=outer_boolean.name)

        bpy.data.objects.remove(outer_tube, do_unlink=True)
        tubular_layers.append(inner_tube)
    
    if tubular_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in tubular_layers:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = tubular_layers[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Tubule_Shell"

generate_tubules()
