# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_Blender_code_that_generates_a_model_of_a_tubular_structure_with_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write Blender code that generates a model of a tubular structure with layers.

import bpy
import math

# Clear any existing objects from the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
number_of_tubules = 9  # Total number of tubules
layer_thickness_value = 0.07  # Thickness of layer around each tubule

def create_tubular_grid():
    # This function constructs a cube with a grid of tubules surrounded by a layer.
    # Steps:
    # 1. Create a cube.
    # 2. Position tubules in a grid.
    # 3. Create inner and outer tubules for each grid position.
    # 4. Apply Boolean modifiers to subtract inner tubules from the cube.
    # 5. Create a hollow layer around each tubule.

    # Initialize a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    # Determine grid dimensions
    grid_dim = math.ceil(math.sqrt(number_of_tubules))
    spacing = 2 / grid_dim
    start_offset = -1 + spacing / 2
    
    # Generate positions for the tubules
    positions = [(start_offset + (i % grid_dim) * spacing, 
                  start_offset + (i // grid_dim) * spacing) 
                 for i in range(number_of_tubules)]
    
    # List to hold tubule objects
    tubule_objects = []
    
    # Iterate through positions to create and subtract tubules
    for x_pos, y_pos in positions:
        # Create an inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x_pos, y_pos, 0))
        inner_tubule = bpy.context.object

        # Create an outer tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness_value, depth=2, location=(x_pos, y_pos, 0))
        outer_tubule = bpy.context.object
        
        # Boolean modifier to subtract inner tubule from the cube
        cube_modifier = main_cube.modifiers.new(name=f"Bool_Cube_{{x_pos}}_{{y_pos}}", type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        # Boolean modifier for creating the hollow layer
        layer_modifier = inner_tubule.modifiers.new(name=f"Bool_Layer_{{x_pos}}_{{y_pos}}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)

        # Clean up the outer tubule
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        
        # Store the inner tubule
        tubule_objects.append(inner_tubule)
    
    # Merge all tubule objects into one
    if tubule_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in tubule_objects:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = tubule_objects[0]
        bpy.ops.object.join()
        final_tubular_structure = bpy.context.object
        final_tubular_structure.name = "Final_Tubular_Structure"

# Execute the tubular grid creation function
create_tubular_grid()
