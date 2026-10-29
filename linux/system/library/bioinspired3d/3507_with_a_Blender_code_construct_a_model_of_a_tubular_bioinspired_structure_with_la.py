# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_code_construct_a_model_of_a_tubular_bioinspired_structure_with_la" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender code construct a model of a tubular bioinspired structure with layers around each tubule.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
num_tubes = 16  # Total number of tubules
layer_thickness_value = 0.04  # Thickness of layer around each tubule

# Function to create the tubular structure

def create_tubular_structure():
    # Add a base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base = bpy.context.object
    
    # Determine grid layout
    grid_dim = math.ceil(math.sqrt(num_tubes))
    spacing = 2 / grid_dim
    start_pos = -1 + spacing / 2
    
    # Calculate positions for tubules
    positions_list = [(start_pos + (i % grid_dim) * spacing,
                       start_pos + (i // grid_dim) * spacing)
                      for i in range(num_tubes)]
    
    # List to hold created tubules
    created_tubules = []
    
    for pos_x, pos_y in positions_list:
        # Create inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_tubule = bpy.context.object
        
        # Create outer tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness_value, depth=2, location=(pos_x, pos_y, 0))
        outer_tubule = bpy.context.object
        
        # Boolean modifier to subtract inner from cube
        boolean_modifier = base.modifiers.new(name=f'Base_Bool_{pos_x}_{pos_y}', type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = base
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        
        # Boolean modifier for hollow layer
        layer_modifier = inner_tubule.modifiers.new(name=f'Layer_Bool_{pos_x}_{pos_y}', type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)
        
        # Remove the outer tubule
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        created_tubules.append(inner_tubule)
    
    # Join all created tubules into a single object
    if created_tubules:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in created_tubules:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = created_tubules[0]
        bpy.ops.object.join()
        combined_tubule = bpy.context.object
        combined_tubule.name = 'Tubular_Structure'

# Create the tubular structure
create_tubular_structure()
