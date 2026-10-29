# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_python_blender_code__create_a_model_of_a_tubular_porous_bioinspired_structu" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with python blender code, create a model of a tubular porous bioinspired structure with layers

import bpy
import math

# Clear the scene of any existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define parameters for the tubular assembly
num_tubules = 20  # Total number of tubules
layer_thickness = 0.06  # Thickness of the layer around each tubule

def build_tubules():
    # Builds a cube with a grid of tubules each surrounded by a layer.
    # Steps:
    # 1. Create a base cube.
    # 2. Arrange tubules in a grid.
    # 3. Generate inner and outer tubules for each position.
    # 4. Apply Boolean modifiers to subtract inner tubules from the cube.
    # 5. Create a hollow layer around each tubule.

    # Create the initial cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Calculate grid size
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    # Generate positions for tubules
    positions = [(start_offset + (i % grid_size) * spacing, 
                  start_offset + (i // grid_size) * spacing) 
                 for i in range(num_tubules)]
    
    # List to hold created tubules
    created_tubules = []
    
    # Iterate through positions to create and subtract tubules
    for pos_x, pos_y in positions:
        # Create inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_tubule = bpy.context.object

        # Create outer tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(pos_x, pos_y, 0))
        outer_tubule = bpy.context.object
        
        # Boolean modifier to subtract inner tubule from the cube
        cube_modifier = base_cube.modifiers.new(name=f"Cube_Bool_{{pos_x}}_{{pos_y}}", type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        # Boolean modifier for creating the hollow layer
        layer_modifier = inner_tubule.modifiers.new(name=f"Layer_Bool_{{pos_x}}_{{pos_y}}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)

        # Remove the outer tubule after processing
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        
        # Store the inner tubule
        created_tubules.append(inner_tubule)
    
    # Merge all created tubules into a single object
    if created_tubules:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in created_tubules:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = created_tubules[0]
        bpy.ops.object.join()
        final_structure = bpy.context.object
        final_structure.name = "Complete_Tubule_Structure"

# Execute the tubule building function
build_tubules()
