# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_blender_code_that_generates_a_tubular_bioinspired_structure_with_cortica" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a blender code that generates a tubular bioinspired structure with cortical layers.

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define structure parameters
num_tubes = 25  # Number of tubules
thickness_of_layer = 0.03  # Thickness of the layer around each tubule

def construct_tubules():
    # Main function to build the tubular structure
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(num_tubes))
    spacing = 2 / grid_dimension
    offset = -1 + spacing / 2
    coordinates = [
        (offset + (i % grid_dimension) * spacing,
         offset + (i // grid_dimension) * spacing)
        for i in range(num_tubes)
    ]
    tubule_layers = []
    for x, y in coordinates:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - thickness_of_layer, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object
        cube_modifier = main_cube.modifiers.new(name=f"Cube_Bool_{x}_{y}", type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tube
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        layer_modifier = inner_tube.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)
        bpy.data.objects.remove(outer_tube, do_unlink=True)
        tubule_layers.append(inner_tube)
    if tubule_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in tubule_layers:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = tubule_layers[0]
        bpy.ops.object.join()
        final_structure = bpy.context.object
        final_structure.name = "Tubule_Structure"

# Execute tubule construction
construct_tubules()
