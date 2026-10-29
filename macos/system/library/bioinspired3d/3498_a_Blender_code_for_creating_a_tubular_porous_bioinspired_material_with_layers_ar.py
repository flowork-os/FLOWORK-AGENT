# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_creating_a_tubular_porous_bioinspired_material_with_layers_ar" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for creating a tubular porous bioinspired material with layers around each tubule.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular formation
num_tubules = 12
layer_thickness = 0.06

def construct_tubular_grid():
    # This function constructs a grid of tubes within a cubic structure.
    # Process:
    # 1. Create a base cube.
    # 2. Calculate positions for each tubule in the grid.
    # 3. Generate inner and outer tubules.
    # 4. Use Boolean modifiers to subtract inner tubules from the cube.
    # 5. Create the hollow layer around the tubules.

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    # Calculate positions for tubules
    tubule_positions = [(start_offset + (i % grid_size) * spacing, 
                         start_offset + (i // grid_size) * spacing) 
                        for i in range(num_tubules)]
    
    created_tubules = []
    
    for position_x, position_y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(position_x, position_y, 0))
        inner_tubule = bpy.context.object
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(position_x, position_y, 0))
        outer_tubule = bpy.context.object
        
        # Apply Boolean operation to subtract inner tubule from the cube
        cube_modifier = base_cube.modifiers.new(name=f"Cube_Bool_{position_x}_{position_y}", type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        # Apply Boolean operation for the hollow layer
        layer_modifier = inner_tubule.modifiers.new(name=f"Layer_Bool_{position_x}_{position_y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)
        
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        created_tubules.append(inner_tubule)
    
    # Join all created tubules into a single object
    if created_tubules:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in created_tubules:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = created_tubules[0]
        bpy.ops.object.join()
        final_tubular_structure = bpy.context.object
        final_tubular_structure.name = "Tubular_Formation"

# Execute the construction of the tubular grid
construct_tubular_grid()
