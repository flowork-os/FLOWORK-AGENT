# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_that_creates_a_model_of_a_tubular_porous_bioinspired_mater" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code that creates a model of a tubular porous bioinspired material with layers around each tubule

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular array
tube_count = 9  # Total number of tubes
layer_thickness_value = 0.07  # Thickness of the layer around each tube

def generate_tubular_array():
    # Create a base cube and subtract tubules
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(tube_count))
    spacing = 2 / grid_dimension
    offset_start = -1 + spacing / 2
    tube_positions = [(offset_start + (i % grid_dimension) * spacing, offset_start + (i // grid_dimension) * spacing) for i in range(tube_count)]
    layer_objects = []
    for pos_x, pos_y in tube_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(pos_x, pos_y, 0))
        inner_tube = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness_value, depth=2, location=(pos_x, pos_y, 0))
        outer_tube = bpy.context.object
        cube_bool = base_cube.modifiers.new(name=f"Cube_Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        cube_bool.operation = 'DIFFERENCE'
        cube_bool.object = inner_tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=cube_bool.name)
        layer_bool = inner_tube.modifiers.new(name=f"Layer_Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        layer_bool.operation = 'DIFFERENCE'
        layer_bool.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=layer_bool.name)
        bpy.data.objects.remove(outer_tube, do_unlink=True)
        layer_objects.append(inner_tube)
    if layer_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for layer in layer_objects:
            layer.select_set(True)
        bpy.context.view_layer.objects.active = layer_objects[0]
        bpy.ops.object.join()
        final_tubular_structure = bpy.context.object
        final_tubular_structure.name = "Final_Tubular_Array"

generate_tubular_array()
