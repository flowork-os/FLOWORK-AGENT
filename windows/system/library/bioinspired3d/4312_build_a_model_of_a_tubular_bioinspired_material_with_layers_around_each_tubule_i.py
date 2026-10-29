# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_a_tubular_bioinspired_material_with_layers_around_each_tubule_i" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of a tubular bioinspired material with layers around each tubule in blender code Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 16  # Total number of tubules in the structure
layer_width = 0.04  # Thickness of layer surrounding each tubule

def build_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(num_tubules))
    gap = 2 / grid_dim
    start_point = -1 + gap / 2
    
    tubule_positions = [(start_point + (i % grid_dim) * gap, 
                         start_point + (i // grid_dim) * gap) 
                        for i in range(num_tubules)]
    
    shell_objects = []
    
    for x, y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object
        
        bool_mod = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        shell_mod = inner_tube.modifiers.new(name=f"Shell_{x}_{y}", type='BOOLEAN')
        shell_mod.operation = 'DIFFERENCE'
        shell_mod.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=shell_mod.name)

        bpy.data.objects.remove(outer_tube, do_unlink=True)

        shell_objects.append(inner_tube)
        
    if shell_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in shell_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = shell_objects[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Final_Shell"

build_tubules()
