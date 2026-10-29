# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_a_tubular_porous_bioinspired_structure_with_layers_around_each_t" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of a tubular porous bioinspired structure with layers around each tubule using Blender Python script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure configuration
total_tubules = 20
thickness_of_layer = 0.04

def generate_tubular_structure():
    # This function constructs a cubic structure with embedded tubules.
    # Steps involved:
    # 1. Create a base cube.
    # 2. Calculate positions for the tubules in a grid.
    # 3. Generate inner and outer tubules at each grid position.
    # 4. Apply Boolean modifiers to carve the inner tubules out of the cube.
    # 5. Create hollow layers around the inner tubules.

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
        
        # Subtract inner tubule from cube
        bool_mod = cube_base.modifiers.new(name=f"Boolean_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_tubule
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        # Create hollow shell around inner tubule
        shell_mod = inner_tubule.modifiers.new(name=f"Shell_{pos_x}_{pos_y}", type='BOOLEAN')
        shell_mod.operation = 'DIFFERENCE'
        shell_mod.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=shell_mod.name)
        
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        tubule_objects.append(inner_tubule)
    
    # Merge all tubules into a single object
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
