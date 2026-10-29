# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_blender_python_code_that_builds_a_model_of_a_cube_of_tubular_material_wit" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create blender python code that builds a model of a cube of tubular material with cortical layers think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
tubule_num = 16  # Number of tubules
layer_size = 0.04  # Thickness of the layer around each tubule

# Function to build the tubule structure
def build_tubules():
    # Create the main cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    # Calculate the grid size
    grid_count = math.ceil(math.sqrt(tubule_num))
    separation = 2 / grid_count
    offset = -1 + separation / 2
    
    # Determine the positions for the tubules
    tubule_locations = [(offset + (i % grid_count) * separation,
                         offset + (i // grid_count) * separation)
                        for i in range(tubule_num)]
    
    # Store processed objects for merging
    processed_tubules = []
    
    for loc_x, loc_y in tubule_locations:
        # Create inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(loc_x, loc_y, 0))
        inner_tubule = bpy.context.object
        
        # Create outer tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_size, depth=2, location=(loc_x, loc_y, 0))
        outer_tubule = bpy.context.object
        
        # Boolean operation to subtract inner from cube
        cube_boolean = main_cube.modifiers.new(name=f'Cube_Bool_{loc_x}_{loc_y}', type='BOOLEAN')
        cube_boolean.operation = 'DIFFERENCE'
        cube_boolean.object = inner_tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=cube_boolean.name)
        
        # Boolean operation to create layer
        layer_boolean = inner_tubule.modifiers.new(name=f'Layer_Bool_{loc_x}_{loc_y}', type='BOOLEAN')
        layer_boolean.operation = 'DIFFERENCE'
        layer_boolean.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_boolean.name)
        
        # Remove outer tubule after processing
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        processed_tubules.append(inner_tubule)
    
    # Join all processed tubules into one
    if processed_tubules:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in processed_tubules:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = processed_tubules[0]
        bpy.ops.object.join()
        final_tubule = bpy.context.object
        final_tubule.name = 'Combined_Tubule_Structure'

# Call the function to build the tubules
build_tubules()
