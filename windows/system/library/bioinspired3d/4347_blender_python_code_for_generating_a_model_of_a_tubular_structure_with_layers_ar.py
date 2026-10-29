# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_generating_a_model_of_a_tubular_structure_with_layers_ar" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for generating a model of a tubular structure with layers around each tubule. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular arrangement
num_tubules = 16  # Total number of tubules
layer_width = 0.05  # Thickness of the layer surrounding each tubule

def build_tubules():
    # Construct a cube and embed tubules in a grid
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    
    positions = [(offset + (i % grid_dim) * spacing, offset + (i // grid_dim) * spacing) for i in range(num_tubules)]
    
    shells = []
    
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object
        
        bool_mod_inner = main_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod_inner.operation = 'DIFFERENCE'
        bool_mod_inner.object = inner_tube
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod_inner.name)
        
        bool_mod_outer = inner_tube.modifiers.new(name=f"Bool_Layer_{x}_{y}", type='BOOLEAN')
        bool_mod_outer.operation = 'DIFFERENCE'
        bool_mod_outer.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=bool_mod_outer.name)
        
        bpy.data.objects.remove(outer_tube, do_unlink=True)
        shells.append(inner_tube)
    
    if shells:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in shells:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = shells[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Final_Shell"

# Create the tubular structure
build_tubules()
