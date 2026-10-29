# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_generating_a_model_of_a_cube_of_tubular_material_with_tu" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for generating a model of a cube of tubular material with tubule layers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular structure
num_tubules = 16  # Total number of tubules
layer_width = 0.05  # Thickness of layer surrounding each tubule

def create_tubular_structure():
    # Function to create a cube with a grid of tubules surrounded by a layer.
    # Steps:
    # 1. Create a cube.
    # 2. Arrange tubules in a grid.
    # 3. Create inner and outer tubules for each position.
    # 4. Use Boolean modifiers for subtraction.

    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    # Determine grid size for tubules
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    # Calculate positions for each tubule
    tubule_positions = [
        (offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing)
        for i in range(num_tubules)
    ]
    
    # List to hold objects for merging
    shell_objects = []
    
    # Process each position for tubules
    for x, y in tubule_positions:
        # Create inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object
        
        # Create outer layer tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        
        # Apply Boolean modifier to subtract inner tubule from cube
        bool_mod_cube = main_cube.modifiers.new(name=f'Bool_Cube_{x}_{y}', type='BOOLEAN')
        bool_mod_cube.operation = 'DIFFERENCE'
        bool_mod_cube.object = inner_tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod_cube.name)
        
        # Apply Boolean modifier to create hollow shell
        bool_mod_shell = inner_tubule.modifiers.new(name=f'Bool_Shell_{x}_{y}', type='BOOLEAN')
        bool_mod_shell.operation = 'DIFFERENCE'
        bool_mod_shell.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=bool_mod_shell.name)

        # Remove outer tubule after processing
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        
        # Add processed tubule to shell objects
        shell_objects.append(inner_tubule)
    
    # Join all tubule shells into one object
    if shell_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in shell_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = shell_objects[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = 'Final_Tubular_Shell'

# Create the tubular structure
create_tubular_structure()
