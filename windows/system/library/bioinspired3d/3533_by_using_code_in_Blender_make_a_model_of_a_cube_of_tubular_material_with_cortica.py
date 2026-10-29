# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_code_in_Blender_make_a_model_of_a_cube_of_tubular_material_with_cortica" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using code in Blender make a model of a cube of tubular material with cortical layers.

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular framework
tubule_quantity = 25  # Number of tubules
shell_thickness = 0.03  # Thickness of the shell around each tubule

def construct_tubules():
    # This function builds a cube with a grid of tubules surrounded by a shell.
    # Process:
    # 1. Create a base cube.
    # 2. Position tubules in a grid.
    # 3. Create inner and outer tubules for each grid point.
    # 4. Apply Boolean operations to subtract inner tubules from the cube.
    # 5. Create a shell by subtracting outer from inner tubules.

    # Start by generating a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    
    # Calculate grid size
    grid_dim = math.ceil(math.sqrt(tubule_quantity))
    spacing = 2 / grid_dim
    start = -1 + spacing / 2
    
    # Generate tubule positions
    tubule_positions = [(start + (i % grid_dim) * spacing, 
                         start + (i // grid_dim) * spacing) 
                        for i in range(tubule_quantity)]
    
    # List for storing created tubules
    created_tubules = []
    
    # Loop through positions to create and subtract tubules
    for pos_x, pos_y in tubule_positions:
        # Create inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_tubule = bpy.context.object

        # Create outer tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - shell_thickness, depth=2, location=(pos_x, pos_y, 0))
        outer_tubule = bpy.context.object
        
        # Boolean modifier to subtract inner tubule from the cube
        bool_modifier = cube_base.modifiers.new(name=f"Inner_Bool_{{pos_x}}_{{pos_y}}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Boolean modifier for shell creation
        shell_modifier = inner_tubule.modifiers.new(name=f"Shell_Bool_{{pos_x}}_{{pos_y}}", type='BOOLEAN')
        shell_modifier.operation = 'DIFFERENCE'
        shell_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=shell_modifier.name)

        # Remove the outer tubule after processing
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        
        # Store the inner tubule
        created_tubules.append(inner_tubule)
    
    # Combine all inner tubules into a single object
    if created_tubules:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in created_tubules:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = created_tubules[0]
        bpy.ops.object.join()
        combined_shell = bpy.context.object
        combined_shell.name = "Combined_Tubule_Shell"

# Run the tubule construction
construct_tubules()
