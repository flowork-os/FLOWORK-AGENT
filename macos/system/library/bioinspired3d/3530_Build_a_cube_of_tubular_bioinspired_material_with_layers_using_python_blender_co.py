# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_cube_of_tubular_bioinspired_material_with_layers_using_python_blender_co" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a cube of tubular bioinspired material with layers using python blender code

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular structure
number_of_tubules = 20  # Total number of tubules
layer_thickness_value = 0.06  # Thickness of layer surrounding each tubule

def create_tubular_structure():
    # Create a cube as the initial object
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid size for tubules
    grid_size = math.ceil(math.sqrt(number_of_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    # Generate coordinates for tubules in the grid
    tubule_coordinates = [(offset + (i % grid_size) * spacing,
                          offset + (i // grid_size) * spacing)
                         for i in range(number_of_tubules)]
    
    # List to store layer objects for merging
    layer_objects = []
    
    # Loop through coordinates to create and subtract cylinders from the cube
    for pos_x, pos_y in tubule_coordinates:
        # Create inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_tubule = bpy.context.object

        # Create outer tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness_value, depth=2, location=(pos_x, pos_y, 0))
        outer_tubule = bpy.context.object
        
        # Subtract the inner tubule from the cube
        bool_mod = base_cube.modifiers.new(name=f'bool_{pos_x}_{pos_y}', type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        # Create hollow shell around the tubule
        shell_mod = inner_tubule.modifiers.new(name=f'shell_{pos_x}_{pos_y}', type='BOOLEAN')
        shell_mod.operation = 'DIFFERENCE'
        shell_mod.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=shell_mod.name)

        # Remove the outer tubule object after subtraction
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        
        # Append the processed inner tubule to the list
        layer_objects.append(inner_tubule)

    # Merge all processed layers into a single object
    if layer_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in layer_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = layer_objects[0]
        bpy.ops.object.join()
        final_layer = bpy.context.object
        final_layer.name = 'Layer_Shell'

# Execute the function to create the tubular structure
create_tubular_structure()
