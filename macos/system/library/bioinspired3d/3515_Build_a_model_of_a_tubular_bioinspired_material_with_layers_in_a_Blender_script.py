# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_a_tubular_bioinspired_material_with_layers_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of a tubular bioinspired material with layers in a Blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular design
total_tubules = 25  # Number of tubules to create
layer_thickness = 0.03  # Thickness of the layer

def generate_tubules():
    # Create a base cube and add a grid of tubules
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_dimension
    start_position = -1 + spacing / 2
    
    tubule_positions = [(start_position + (i % grid_dimension) * spacing, start_position + (i // grid_dimension) * spacing) for i in range(total_tubules)]
    
    created_shells = []
    
    for pos_x, pos_y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_cylinder = bpy.context.object
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(pos_x, pos_y, 0))
        outer_cylinder = bpy.context.object
        
        bool_modifier = cube_base.modifiers.new(name=f"Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_cylinder
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        outer_bool_mod = inner_cylinder.modifiers.new(name=f"Outer_Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        outer_bool_mod.operation = 'DIFFERENCE'
        outer_bool_mod.object = outer_cylinder
        bpy.context.view_layer.objects.active = inner_cylinder
        bpy.ops.object.modifier_apply(modifier=outer_bool_mod.name)
        
        bpy.data.objects.remove(outer_cylinder, do_unlink=True)
        created_shells.append(inner_cylinder)
    
    if created_shells:
        bpy.ops.object.select_all(action='DESELECT')
        for shell in created_shells:
            shell.select_set(True)
        bpy.context.view_layer.objects.active = created_shells[0]
        bpy.ops.object.join()
        final_object = bpy.context.object
        final_object.name = "Tubule_Shell"

# Execute the tubule generation
generate_tubules()
