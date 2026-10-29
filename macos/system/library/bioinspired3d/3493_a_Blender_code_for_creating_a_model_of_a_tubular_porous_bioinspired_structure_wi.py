# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_creating_a_model_of_a_tubular_porous_bioinspired_structure_wi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for creating a model of a tubular porous bioinspired structure with tubule layers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular assembly
count_tubules = 12  # Total number of tubules
thickness_of_layer = 0.07  # Thickness of the layer around each tubule

def construct_tubules():
    # Function to build a cube with a grid of tubules surrounded by a layer.
    # Summary:
    # 1. Add a cube.
    # 2. Position tubules in a grid.
    # 3. Create inner and outer tubules for each grid position.
    # 4. Use Boolean modifiers to finalize the geometry.

    # Create a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    
    # Calculate grid size
    grid_dimension = math.ceil(math.sqrt(count_tubules))
    spacing = 2 / grid_dimension
    offset = -1 + spacing / 2
    
    # Generate positions for tubules
    positions = [
        (offset + (i % grid_dimension) * spacing, offset + (i // grid_dimension) * spacing)
        for i in range(count_tubules)
    ]
    
    # List to hold the tubule objects
    tubule_list = []
    
    # Loop through positions to create tubules
    for pos_x, pos_y in positions:
        # Create inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_cylinder = bpy.context.object
        
        # Create outer layer tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - thickness_of_layer, depth=2, location=(pos_x, pos_y, 0))
        outer_cylinder = bpy.context.object
        
        # Apply Boolean modifier to cube
        cube_modifier = cube_base.modifiers.new(name=f'Cube_Bool_{pos_x}_{pos_y}', type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_cylinder
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        # Apply Boolean modifier to inner tubule
        inner_modifier = inner_cylinder.modifiers.new(name=f'Inner_Bool_{pos_x}_{pos_y}', type='BOOLEAN')
        inner_modifier.operation = 'DIFFERENCE'
        inner_modifier.object = outer_cylinder
        bpy.context.view_layer.objects.active = inner_cylinder
        bpy.ops.object.modifier_apply(modifier=inner_modifier.name)

        # Remove outer tubule after processing
        bpy.data.objects.remove(outer_cylinder, do_unlink=True)
        
        # Store processed inner tubule
        tubule_list.append(inner_cylinder)
    
    # Join all inner tubules into one object
    if tubule_list:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in tubule_list:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = tubule_list[0]
        bpy.ops.object.join()
        final_tubular_object = bpy.context.object
        final_tubular_object.name = 'Tubular_Assembly_Final'

# Execute the construction of tubules
construct_tubules()
