# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_a_tubular_bioinspired_material_with_tubule_layers_in_python_blen" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of a tubular bioinspired material with tubule layers in python blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration of the tubular structure
tubule_count = 25  # Total number of tubules
layer_thickness = 0.03  # Thickness of the surrounding layer

def create_tubule_structure():
    # Function to build a cube with a grid of tubules and their layers.
    # Steps involved:
    # 1. Initialize a cube.
    # 2. Arrange tubules in a grid.
    # 3. Create inner/outer tubules for each position.
    # 4. Use Boolean operations to subtract inner tubules from the cube.
    # 5. Subtract outer from inner to form the layer.

    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    
    # Determine the grid size for the tubules
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    # Generate positions for tubules
    positions = [(offset + (i % grid_size) * spacing,
                  offset + (i // grid_size) * spacing)
                 for i in range(tubule_count)]
    
    # Store objects for merging later
    tubule_layers = []
    
    # Iterate over each position to create tubules
    for x, y in positions:
        # Add a tubule at the calculated position
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object

        # Add an outer tubule layer
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        
        # Apply Boolean modifier for the inner tubule
        cube_modifier = cube_object.modifiers.new(name=f"Cube_Bool_{x}_{y}", type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        # Apply Boolean modifier for the outer layer
        layer_modifier = inner_tubule.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)

        # Clean up the outer tubule
        bpy.data.objects.remove(outer_tubule, do_unlink=True)

        # Collect the inner tubule for later merging
        tubule_layers.append(inner_tubule)
    
    # Merge all the layers into one object
    if tubule_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in tubule_layers:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = tubule_layers[0]
        bpy.ops.object.join()
        final_object = bpy.context.object
        final_object.name = "Merged_Tubule_Shell"

# Call the function to create the structure
create_tubule_structure()
