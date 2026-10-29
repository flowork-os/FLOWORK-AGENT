# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_tubular_porous_material_with_layers_using_code_in_Blender_think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a tubular porous material with layers using code in Blender think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure configuration
total_tubules = 20
thickness_of_layer = 0.04

def generate_tubular_structure():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    grid_dim = math.ceil(math.sqrt(total_tubules))
    interval = 2 / grid_dim
    initial_position = -1 + interval / 2
    
    positions = [(initial_position + (i % grid_dim) * interval, 
                   initial_position + (i // grid_dim) * interval) 
                  for i in range(total_tubules)]
    
    tubule_objects = []
    
    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_tubule = bpy.context.object
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - thickness_of_layer, depth=2, location=(pos_x, pos_y, 0))
        outer_tubule = bpy.context.object
        
        bool_mod = cube_base.modifiers.new(name=f"Boolean_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_tubule
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        shell_mod = inner_tubule.modifiers.new(name=f"Shell_{pos_x}_{pos_y}", type='BOOLEAN')
        shell_mod.operation = 'DIFFERENCE'
        shell_mod.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=shell_mod.name)
        
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        tubule_objects.append(inner_tubule)
    
    if tubule_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in tubule_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = tubule_objects[0]
        bpy.ops.object.join()
        final_structure = bpy.context.object
        final_structure.name = "Final_Tubular_Structure"

# Create the tubular structure
generate_tubular_structure()
