# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_python_blender_code__construct_a_tubular_porous_material_with_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using python blender code, construct a tubular porous material with layers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
num_of_tubules = 16  # Total number of tubules
layer_thickness_value = 0.04  # Thickness of layer surrounding each tubule

# Function to create the tubular structure

def generate_tubular_structure():
    # Create base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid layout
    grid_size = math.ceil(math.sqrt(num_of_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    # Calculate positions for the tubules
    tubule_positions = [(start_offset + (i % grid_size) * spacing,
                         start_offset + (i // grid_size) * spacing)
                        for i in range(num_of_tubules)]
    
    # List to hold created tubules
    created_tubules = []
    
    for pos_x, pos_y in tubule_positions:
        # Create inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_tubule = bpy.context.object
        
        # Create outer tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness_value, depth=2, location=(pos_x, pos_y, 0))
        outer_tubule = bpy.context.object
        
        # Boolean modifier to subtract inner from cube
        bool_modifier = base_cube.modifiers.new(name=f'Bool_{pos_x}_{pos_y}', type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Boolean modifier to create hollow layer
        layer_modifier = inner_tubule.modifiers.new(name=f'Layer_Bool_{pos_x}_{pos_y}', type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)
        
        # Remove outer tubule after processing
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        created_tubules.append(inner_tubule)
    
    # Join all created tubules into one
    if created_tubules:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in created_tubules:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = created_tubules[0]
        bpy.ops.object.join()
        final_tubule = bpy.context.object
        final_tubule.name = 'Combined_Tubule_Structure'

# Call the function to generate the tubular structure
generate_tubular_structure()
