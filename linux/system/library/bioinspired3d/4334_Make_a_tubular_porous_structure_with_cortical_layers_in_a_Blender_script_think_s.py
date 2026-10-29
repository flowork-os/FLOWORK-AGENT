# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_tubular_porous_structure_with_cortical_layers_in_a_Blender_script_think_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a tubular porous structure with cortical layers in a Blender script think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular structure
number_of_tubules = 20  # Number of tubules
layer_thickness_value = 0.04  # Thickness of the layer

def build_tubule_grid():
    # Add a cube as the base object
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Calculate grid size for tubules
    grid_size = math.ceil(math.sqrt(number_of_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    # Generate tubule positions
    positions = [(offset + (i % grid_size) * spacing,
                  offset + (i // grid_size) * spacing)
                 for i in range(number_of_tubules)]
    
    # List to hold layer objects
    layer_objects = []
    
    # Loop through each position to create tubules
    for x, y in positions:
        # Create an inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object

        # Create an outer tubule layer
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness_value, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        
        # Apply Boolean modifier to subtract the inner tubule from the cube
        bool_modifier = base_cube.modifiers.new(name=f"Cube_Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Apply Boolean modifier to create the hollow shell
        layer_modifier = inner_tubule.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)

        # Remove the outer tubule after subtraction
        bpy.data.objects.remove(outer_tubule, do_unlink=True)

        # Store the processed inner tubule for merging
        layer_objects.append(inner_tubule)
    
    # Merge all tubule layers into one object
    if layer_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in layer_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = layer_objects[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Final_Tubule_Structure"

# Execute the tubule grid creation
build_tubule_grid()
