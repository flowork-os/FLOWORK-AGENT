# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_to_make_a_model_of_a_cube_of_tubular_material_with_layers_around" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script to make a model of a cube of tubular material with layers around each tubule think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular formation
num_tubules = 12
layer_thickness = 0.06

def construct_tubular_grid():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    tubule_positions = [(start_offset + (i % grid_size) * spacing, 
                         start_offset + (i // grid_size) * spacing) 
                        for i in range(num_tubules)]
    
    created_tubules = []
    
    for position_x, position_y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(position_x, position_y, 0))
        inner_tubule = bpy.context.object
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(position_x, position_y, 0))
        outer_tubule = bpy.context.object
        
        cube_modifier = base_cube.modifiers.new(name=f"Cube_Bool_{position_x}_{position_y}", type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        layer_modifier = inner_tubule.modifiers.new(name=f"Layer_Bool_{position_x}_{position_y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)
        
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        created_tubules.append(inner_tubule)
    
    if created_tubules:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in created_tubules:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = created_tubules[0]
        bpy.ops.object.join()
        final_tubular_structure = bpy.context.object
        final_tubular_structure.name = "Tubular_Formation"

construct_tubular_grid()
