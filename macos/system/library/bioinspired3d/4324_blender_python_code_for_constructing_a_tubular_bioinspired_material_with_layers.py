# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_constructing_a_tubular_bioinspired_material_with_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for constructing a tubular bioinspired material with layers. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
number_of_tubules = 20  # Number of tubules
layer_thickness_value = 0.03  # Thickness of the layer around each tubule

def generate_tubular_structure():
    # Create a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Calculate grid size
    grid_count = math.ceil(math.sqrt(number_of_tubules))
    spacing = 2 / grid_count
    offset_start = -1 + spacing / 2
    
    # Generate positions for tubules
    tubule_locations = [
        (offset_start + (i % grid_count) * spacing, offset_start + (i // grid_count) * spacing)
        for i in range(number_of_tubules)
    ]
    
    # List to hold tubule objects
    tubule_objects = []
    
    # Iterate through positions to create tubules
    for pos_x, pos_y in tubule_locations:
        # Create inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_tubule = bpy.context.object
        
        # Create outer layer tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness_value, depth=2, location=(pos_x, pos_y, 0))
        outer_tubule = bpy.context.object
        
        # Apply Boolean operation to cube
        cube_bool = base_cube.modifiers.new(name=f'Cube_Bool_{pos_x}_{pos_y}', type='BOOLEAN')
        cube_bool.operation = 'DIFFERENCE'
        cube_bool.object = inner_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=cube_bool.name)
        
        # Apply Boolean operation to inner tubule
        inner_bool = inner_tubule.modifiers.new(name=f'Inner_Bool_{pos_x}_{pos_y}', type='BOOLEAN')
        inner_bool.operation = 'DIFFERENCE'
        inner_bool.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=inner_bool.name)

        # Delete outer tubule after processing
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        
        # Add inner tubule to the list
        tubule_objects.append(inner_tubule)
    
    # Join all inner tubules into one object
    if tubule_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in tubule_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = tubule_objects[0]
        bpy.ops.object.join()
        final_structure = bpy.context.object
        final_structure.name = 'Final_Tubular_Assembly'

# Run the tubular structure generation
generate_tubular_structure()
