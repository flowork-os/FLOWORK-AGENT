# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_Blender_code_that_generates_a_tubular_bioinspired_material_with_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a Blender code that generates a tubular bioinspired material with layers around each tubule. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
total_tubules = 12  # Total number of tubules
layer_thickness_value = 0.06  # Thickness of the layer

def construct_tubule_grid():
    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine the grid size for the tubules
    grid_size = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    # Generate positions for tubules
    positions = [(offset + (i % grid_size) * spacing,
                  offset + (i // grid_size) * spacing)
                 for i in range(total_tubules)]
    
    # List for storing layer objects
    layer_objects = []
    
    # Iterate over each position to create tubules
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness_value, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        
        # Apply Boolean modifier for the inner tubule
        cube_modifier = base_cube.modifiers.new(name=f"Cube_Bool_{x}_{y}", type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = base_cube
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
        layer_objects.append(inner_tubule)
    
    # Merge all the layers into one object
    if layer_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in layer_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = layer_objects[0]
        bpy.ops.object.join()
        final_object = bpy.context.object
        final_object.name = "Combined_Tubule_Structure"

# Call the function to create the structure
construct_tubule_grid()
