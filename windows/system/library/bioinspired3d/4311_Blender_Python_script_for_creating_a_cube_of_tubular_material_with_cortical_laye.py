# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_for_creating_a_cube_of_tubular_material_with_cortical_laye" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script for creating a cube of tubular material with cortical layers think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for tubular structure
total_tubules = 18  # Number of tubules
layer_thickness = 0.07  # Thickness of the layer surrounding each tubule

# Main function to create the structure
def construct_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(total_tubules)]
    layer_objects = []
    
    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        
        # Boolean operation to subtract inner tubule from cube
        bool_mod = main_cube.modifiers.new(name=f"Cube_Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        # Create hollow shell around the tubule
        layer_mod = inner_tubule.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_mod.operation = 'DIFFERENCE'
        layer_mod.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_mod.name)
        
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        layer_objects.append(inner_tubule)
    
    # Merge all layer objects into one
    if layer_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for layer in layer_objects:
            layer.select_set(True)
        bpy.context.view_layer.objects.active = layer_objects[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Final_Tubule_Shell"

# Generate the tubular structure
construct_tubules()
