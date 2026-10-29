# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_Python_script__make_a_model_of_a_tubular_porous_bioinspired_struct" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender Python script, make a model of a tubular porous bioinspired structure with layers around each tubule think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
count_of_tubules = 25  # Total number of tubules
thickness_of_layer = 0.03  # Thickness of layer surrounding each tubule

def build_tubules():
    # Create a cube as the foundation object
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    foundation_cube = bpy.context.object
    
    # Determine grid size for tubules
    grid_count = math.ceil(math.sqrt(count_of_tubules))
    distance_between_tubules = 2 / grid_count
    offset_start = -1 + distance_between_tubules / 2
    
    # Generate positions for tubules in the grid
    tubule_coordinates = [(offset_start + (i % grid_count) * distance_between_tubules,
                          offset_start + (i // grid_count) * distance_between_tubules)
                         for i in range(count_of_tubules)]
    
    # Store processed layer objects
    layer_objects = []
    
    # Iterate through coordinates to create and subtract cylinders from the cube
    for pos_x, pos_y in tubule_coordinates:
        # Create a cylinder (tubule) at the specified position
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_tubule_instance = bpy.context.object

        # Create an outer layer at the same position
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - thickness_of_layer, depth=2, location=(pos_x, pos_y, 0))
        outer_tubule_instance = bpy.context.object
        
        # Apply Boolean subtraction to remove the inner tubule from the cube
        cube_modifier = foundation_cube.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tubule_instance
        bpy.context.view_layer.objects.active = foundation_cube
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        # Apply Boolean subtraction to create the hollow shell around the tubule
        shell_modifier = inner_tubule_instance.modifiers.new(name=f"Shell_{pos_x}_{pos_y}", type='BOOLEAN')
        shell_modifier.operation = 'DIFFERENCE'
        shell_modifier.object = outer_tubule_instance
        bpy.context.view_layer.objects.active = inner_tubule_instance
        bpy.ops.object.modifier_apply(modifier=shell_modifier.name)

        # Remove the outer tubule object after subtraction
        bpy.data.objects.remove(outer_tubule_instance, do_unlink=True)
        
        # Append the processed inner tubule to the list
        layer_objects.append(inner_tubule_instance)
        
    # Merge all processed layers into a single object
    if layer_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in layer_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = layer_objects[0]
        bpy.ops.object.join()
        final_layer_shell = bpy.context.object
        final_layer_shell.name = "Layer_Shell"

# Execute the tubule generation function
build_tubules()
