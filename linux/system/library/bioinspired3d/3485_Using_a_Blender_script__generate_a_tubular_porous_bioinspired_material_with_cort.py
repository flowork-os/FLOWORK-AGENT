# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_Blender_script__generate_a_tubular_porous_bioinspired_material_with_cort" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a Blender script, generate a tubular porous bioinspired material with cortical layers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure configuration
num_tubules = 22  # Total number of tubules
layer_thickness = 0.07  # Thickness of layer surrounding each tubule

def construct_tubules():
    # Builds a cube with a grid of tubules surrounded by a layer.
    # Steps:
    # 1. Create a cube.
    # 2. Arrange tubules in a grid.
    # 3. Generate inner and outer tubules for each position.
    # 4. Use Boolean modifiers to subtract inner tubules from the cube.
    # 5. Use Boolean modifiers to create a hollow layer around each tubule.

    # Create a cube as the base object
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Calculate grid layout for tubules
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset_start = -1 + spacing / 2
    
    # Calculate positions for tubules
    positions = [(offset_start + (i % grid_size) * spacing, 
                   offset_start + (i // grid_size) * spacing) 
                  for i in range(num_tubules)]
    
    # List to hold created shell objects
    created_shells = []
    
    # Iterate through positions to create and subtract tubules
    for pos_x, pos_y in positions:
        # Create an inner cylinder (tubule)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_tube = bpy.context.object

        # Create an outer cylinder (layer)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(pos_x, pos_y, 0))
        outer_tube = bpy.context.object
        
        # Apply Boolean to remove the inner tube from the cube
        cube_bool = base_cube.modifiers.new(name=f"Cube_Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        cube_bool.operation = 'DIFFERENCE'
        cube_bool.object = inner_tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=cube_bool.name)
        
        # Apply Boolean to create a hollow layer
        inner_bool = inner_tube.modifiers.new(name=f"Inner_Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        inner_bool.operation = 'DIFFERENCE'
        inner_bool.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=inner_bool.name)

        # Remove the outer tube after processing
        bpy.data.objects.remove(outer_tube, do_unlink=True)

        # Store the processed inner tube for merging
        created_shells.append(inner_tube)
        
    # Merge all created shells into one
    if created_shells:
        bpy.ops.object.select_all(action='DESELECT')
        for shell in created_shells:
            shell.select_set(True)
        bpy.context.view_layer.objects.active = created_shells[0]
        bpy.ops.object.join()
        final_tubular_structure = bpy.context.object
        final_tubular_structure.name = "Merged_Tubular_Structure"

# Generate the tubular structure
construct_tubules()
