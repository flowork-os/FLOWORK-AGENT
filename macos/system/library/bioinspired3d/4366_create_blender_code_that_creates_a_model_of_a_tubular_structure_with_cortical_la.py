# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_blender_code_that_creates_a_model_of_a_tubular_structure_with_cortical_la" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create blender code that creates a model of a tubular structure with cortical layers Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular design
num_tubules = 16  # Total number of tubules
layer_width = 0.05  # Thickness of the layer surrounding each tubule

def generate_tubules():
    # This function constructs a cube with a grid of tubules, each encased in a layer.
    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid layout for tubules
    grid_dim = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    
    # Calculate positions for tubules
    tubule_positions = [(offset + (i % grid_dim) * spacing, 
                         offset + (i // grid_dim) * spacing) 
                        for i in range(num_tubules)]
    
    # List to hold tubule layers
    tubule_layers = []
    
    # Create and subtract tubules
    for x, y in tubule_positions:
        # Inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object

        # Outer tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object
        
        # Boolean modifier to subtract inner tubule from the cube
        bool_mod = base_cube.modifiers.new(name=f"Bool_Tube_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        # Boolean modifier to create hollow shell
        shell_mod = inner_tube.modifiers.new(name=f"Shell_Bool_{x}_{y}", type='BOOLEAN')
        shell_mod.operation = 'DIFFERENCE'
        shell_mod.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=shell_mod.name)

        # Clean up outer tubule
        bpy.data.objects.remove(outer_tube, do_unlink=True)
        
        # Add processed inner tubule to the list
        tubule_layers.append(inner_tube)
    
    # Merge all processed tubule layers
    if tubule_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for layer in tubule_layers:
            layer.select_set(True)
        bpy.context.view_layer.objects.active = tubule_layers[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Tubule_Shell"

# Execute tubule generation
generate_tubules()
