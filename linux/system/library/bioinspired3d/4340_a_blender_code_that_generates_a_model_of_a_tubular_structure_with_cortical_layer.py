# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_generates_a_model_of_a_tubular_structure_with_cortical_layer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that generates a model of a tubular structure with cortical layers think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular formation
total_tubules = 16  # Number of tubules
layer_thickness_value = 0.04  # Thickness of the layer around each tubule

# Function to construct the tubules
def construct_tubules():
    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    
    # Calculate grid dimensions
    grid_dimension = math.ceil(math.sqrt(total_tubules))
    spacing_value = 2 / grid_dimension
    offset_value = -1 + spacing_value / 2
    
    # Determine positions for tubules
    tubule_positions = [(offset_value + (i % grid_dimension) * spacing_value,
                         offset_value + (i // grid_dimension) * spacing_value)
                        for i in range(total_tubules)]
    
    # List to store the created tubules
    tubule_objects = []
    
    for position_x, position_y in tubule_positions:
        # Create inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(position_x, position_y, 0))
        inner_tubule = bpy.context.object
        
        # Create outer tubule layer
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness_value, depth=2, location=(position_x, position_y, 0))
        outer_tubule = bpy.context.object
        
        # Apply Boolean modifier to subtract inner from the cube
        cube_modifier = cube_base.modifiers.new(name=f'Cube_Bool_{position_x}_{position_y}', type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        # Apply Boolean modifier to create the hollow layer
        layer_modifier = inner_tubule.modifiers.new(name=f'Layer_Bool_{position_x}_{position_y}', type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)
        
        # Remove the outer tubule
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        tubule_objects.append(inner_tubule)
    
    # Join all tubules into a single object
    if tubule_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in tubule_objects:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = tubule_objects[0]
        bpy.ops.object.join()
        final_structure = bpy.context.object
        final_structure.name = 'Final_Tubule_Structure'

# Execute the construction of the tubules
construct_tubules()
