# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_a_tubular_bioinspired_material_with_layers_using_blender_sc" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of a tubular bioinspired material with layers using blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
count_tubules = 20  # Total number of tubules
layer_width = 0.06  # Width of the layer around each tubule

def create_tubules_grid():
    # Initialize a cube and create a grid of tubules
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(count_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    positions = [(start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing) for i in range(count_tubules)]
    
    shells = []
    
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_cylinder = bpy.context.object
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(x, y, 0))
        outer_cylinder = bpy.context.object
        
        bool_mod = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_cylinder
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        bool_mod_outer = inner_cylinder.modifiers.new(name=f"Outer_Bool_{x}_{y}", type='BOOLEAN')
        bool_mod_outer.operation = 'DIFFERENCE'
        bool_mod_outer.object = outer_cylinder
        bpy.context.view_layer.objects.active = inner_cylinder
        bpy.ops.object.modifier_apply(modifier=bool_mod_outer.name)
        
        bpy.data.objects.remove(outer_cylinder, do_unlink=True)
        shells.append(inner_cylinder)
    
    if shells:
        bpy.ops.object.select_all(action='DESELECT')
        for shell in shells:
            shell.select_set(True)
        bpy.context.view_layer.objects.active = shells[0]
        bpy.ops.object.join()
        final_object = bpy.context.object
        final_object.name = "Complete_Shell"

# Execute the creation of the tubular grid
create_tubules_grid()
