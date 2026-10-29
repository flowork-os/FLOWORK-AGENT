# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_to_build_a_model_of_a_tubular_bioinspired_structure_with_lay" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code to build a model of a tubular bioinspired structure with layers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular setup
count_tubules = 12  # Total number of tubules
layer_thick = 0.05  # Thickness of the layer surrounding each tubule

def assemble_tubules():
    # Constructs a cube with a grid of tubules surrounded by a layer.
    # Overview:
    # 1. Create a cube.
    # 2. Arrange tubules in a grid pattern.
    # 3. Create inner and outer tubules for each position.
    # 4. Use Boolean modifiers to subtract inner tubules from the cube.
    # 5. Use Boolean modifiers to create a hollow shell around the tubule.

    # Add a cube as the base
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    
    # Calculate grid dimensions for tubules
    grid_dim = math.ceil(math.sqrt(count_tubules))
    gap_size = 2 / grid_dim
    start_offset = -1 + gap_size / 2
    
    # Calculate positions for tubules in the grid
    tubule_coords = [(start_offset + (i % grid_dim) * gap_size, 
                      start_offset + (i // grid_dim) * gap_size) 
                     for i in range(count_tubules)]
    
    # List to hold created shell objects
    shell_objects = []
    
    # Loop through coordinates to create and subtract tubules
    for x, y in tubule_coords:
        # Create an inner cylinder (tubule)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object

        # Create an outer cylinder (layer)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thick, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        
        # Apply Boolean to remove the inner tubule from the cube
        bool_mod = cube_base.modifiers.new(name=f"Cube_Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_tubule
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        # Apply Boolean to create a hollow shell around the inner tubule
        inner_bool = inner_tubule.modifiers.new(name=f"Inner_Bool_{x}_{y}", type='BOOLEAN')
        inner_bool.operation = 'DIFFERENCE'
        inner_bool.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=inner_bool.name)

        # Clean up the outer tubule
        bpy.data.objects.remove(outer_tubule, do_unlink=True)

        # Store the processed inner tubule for merging
        shell_objects.append(inner_tubule)
        
    # Merge all shell objects into one
    if shell_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for shell in shell_objects:
            shell.select_set(True)
        bpy.context.view_layer.objects.active = shell_objects[0]
        bpy.ops.object.join()
        final_structure = bpy.context.object
        final_structure.name = "Final_Tubule_Shell"

# Execute the assembly of tubules
assemble_tubules()
