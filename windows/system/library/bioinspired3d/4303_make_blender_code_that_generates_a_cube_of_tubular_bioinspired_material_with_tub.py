# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_blender_code_that_generates_a_cube_of_tubular_bioinspired_material_with_tub" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make blender code that generates a cube of tubular bioinspired material with tubule layers. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
total_tubules = 25  # Total number of tubules
shell_thickness = 0.03  # Thickness of the layer around each tubule

def build_tubules():
    # Initialize with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(total_tubules))
    distance = 2 / grid_dimension
    start_position = -1 + distance / 2
    
    # Calculate positions for the tubules
    tubule_positions = [(start_position + (i % grid_dimension) * distance, 
                         start_position + (i // grid_dimension) * distance) 
                        for i in range(total_tubules)]
    
    created_layers = []
    
    for x, y in tubule_positions:
        # Create the inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object

        # Create the outer layer
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - shell_thickness, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object
        
        # Boolean operation to subtract the inner tubule from the cube
        bool_mod = main_cube.modifiers.new(name=f"Cut_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_tube
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        # Boolean operation for the hollow shell
        shell_bool = inner_tube.modifiers.new(name=f"Shell_Bool_{x}_{y}", type='BOOLEAN')
        shell_bool.operation = 'DIFFERENCE'
        shell_bool.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=shell_bool.name)

        # Delete the outer tubule
        bpy.data.objects.remove(outer_tube, do_unlink=True)
        created_layers.append(inner_tube)
    
    # Merge all created layers into one object
    if created_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in created_layers:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = created_layers[0]
        bpy.ops.object.join()
        final_tubule_shell = bpy.context.object
        final_tubule_shell.name = "Tubule_Outer_Shell"

# Build the tubular formation
build_tubules()
