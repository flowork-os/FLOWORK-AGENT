# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_tubular_porous_material_with_cortical_layers_in_a_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a tubular porous material with cortical layers in a Blender script think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters defining the tubular structure
num_tubules = 16  # Total number of tubules
layer_thickness = 0.04  # Thickness of the layer around each tubule

# Function to construct the tubule structure
def build_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_dimension
    offset = -1 + spacing / 2
    
    positions = [(offset + (i % grid_dimension) * spacing, offset + (i // grid_dimension) * spacing) for i in range(num_tubules)]
    layers = []
    
    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object
        
        bool_modifier = main_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tube
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        layer_modifier = inner_tube.modifiers.new(name=f"Layer_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)
        
        bpy.data.objects.remove(outer_tube, do_unlink=True)
        layers.append(inner_tube)
    
    if layers:
        bpy.ops.object.select_all(action='DESELECT')
        for layer in layers:
            layer.select_set(True)
        bpy.context.view_layer.objects.active = layers[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Final_Layer_Shell"

# Construct the tubular structure
build_tubules()
