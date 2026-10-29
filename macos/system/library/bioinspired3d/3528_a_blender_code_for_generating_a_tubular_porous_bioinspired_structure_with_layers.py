# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_for_generating_a_tubular_porous_bioinspired_structure_with_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code for generating a tubular porous bioinspired structure with layers around each tubule

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters defining the tubular structure
num_tubules = 16  # Total number of tubules
layer_width = 0.05  # Thickness of layer surrounding each tubule

def generate_tubules():
    # Constructs a cube with a grid of tubules, each surrounded by a layer.
    # Steps:
    # 1. Create a cube.
    # 2. Position tubules in a grid.
    # 3. Create inner and outer tubules for each grid position.
    # 4. Apply Boolean modifiers to subtract inner tubules from the cube.
    # 5. Subtract inner tubules from outer tubules to create layers.

    # Create a cube as the base object
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Calculate grid dimensions for tubules
    grid_dimension = math.ceil(math.sqrt(num_tubules))
    spacing_distance = 2 / grid_dimension
    initial_offset = -1 + spacing_distance / 2
    
    # Generate coordinates for tubules in the grid
    tubule_positions = [(initial_offset + (i % grid_dimension) * spacing_distance,
                         initial_offset + (i // grid_dimension) * spacing_distance)
                        for i in range(num_tubules)]
    
    # List to hold layer objects for merging
    processed_layers = []
    
    # Loop through positions to subtract cylinders from the cube
    for x, y in tubule_positions:
        # Create a cylinder (tubule) at the calculated position
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule_obj = bpy.context.object

        # Create a layer at the same position
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(x, y, 0))
        outer_tubule_obj = bpy.context.object
        
        # Apply Boolean subtraction to remove the inner tubule from the cube
        bool_modifier = base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tubule_obj
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Apply Boolean subtraction to create the hollow shell around the tubule
        layer_modifier = inner_tubule_obj.modifiers.new(name=f"Bool_Layer_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule_obj
        bpy.context.view_layer.objects.active = inner_tubule_obj
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)

        # Remove the outer tubule object after subtraction
        bpy.data.objects.remove(outer_tubule_obj, do_unlink=True)
        
        # Store the processed shell object for merging
        processed_layers.append(inner_tubule_obj)
        
    # Merge all layers into a single object
    if processed_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in processed_layers:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = processed_layers[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Layer_Shell"

# Generate tubular structure with layers
generate_tubules()
