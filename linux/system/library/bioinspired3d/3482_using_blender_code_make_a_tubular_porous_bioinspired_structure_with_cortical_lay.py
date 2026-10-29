# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_code_make_a_tubular_porous_bioinspired_structure_with_cortical_lay" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender code make a tubular porous bioinspired structure with cortical layers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
total_tubules = 25  # Total number of tubules
thickness_of_layer = 0.06  # Thickness of layer around each tubule

def generate_tubules():
    # Builds a cube with a grid of tubules surrounded by a layer.
    # Workflow:
    # 1. Create a cube.
    # 2. Arrange tubules in a grid.
    # 3. Create inner and outer tubules for each grid point.
    # 4. Use Boolean modifiers to subtract inner tubules from the cube.
    # 5. Use Boolean modifiers to create a hollow layer around each tubule.

    # Add a cube as the base
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    
    # Determine grid size for tubules
    grid_dimension = math.ceil(math.sqrt(total_tubules))
    spacing_distance = 2 / grid_dimension
    initial_offset = -1 + spacing_distance / 2
    
    # Calculate positions for tubules
    tubule_coordinates = [(initial_offset + (i % grid_dimension) * spacing_distance, 
                           initial_offset + (i // grid_dimension) * spacing_distance) 
                          for i in range(total_tubules)]
    
    # List to hold tubule shells for merging
    tubule_shells = []
    
    # Loop through coordinates to create and subtract tubules
    for pos_x, pos_y in tubule_coordinates:
        # Add an inner cylinder
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_cylinder = bpy.context.object

        # Add an outer cylinder
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - thickness_of_layer, depth=2, location=(pos_x, pos_y, 0))
        outer_cylinder = bpy.context.object
        
        # Apply Boolean to remove the inner cylinder from the cube
        cube_bool = cube_base.modifiers.new(name=f"Cube_Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        cube_bool.operation = 'DIFFERENCE'
        cube_bool.object = inner_cylinder
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=cube_bool.name)
        
        # Apply Boolean to create the hollow layer
        inner_bool = inner_cylinder.modifiers.new(name=f"Inner_Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        inner_bool.operation = 'DIFFERENCE'
        inner_bool.object = outer_cylinder
        bpy.context.view_layer.objects.active = inner_cylinder
        bpy.ops.object.modifier_apply(modifier=inner_bool.name)

        # Clean up the outer cylinder
        bpy.data.objects.remove(outer_cylinder, do_unlink=True)

        # Save the processed inner cylinder for merging
        tubule_shells.append(inner_cylinder)
        
    # Merge all tubule shells
    if tubule_shells:
        bpy.ops.object.select_all(action='DESELECT')
        for shell in tubule_shells:
            shell.select_set(True)
        bpy.context.view_layer.objects.active = tubule_shells[0]
        bpy.ops.object.join()
        final_structure = bpy.context.object
        final_structure.name = "Merged_Tubule_Shell"

# Execute the tubule generation
generate_tubules()
