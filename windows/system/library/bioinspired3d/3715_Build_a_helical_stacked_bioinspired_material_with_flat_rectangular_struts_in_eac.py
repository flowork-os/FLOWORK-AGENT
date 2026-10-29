# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_helical_stacked_bioinspired_material_with_flat_rectangular_struts_in_eac" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a helical stacked bioinspired material with flat rectangular struts in each layer using Blender Python script Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 12  # Total number of layers
rotation_angle = 15  # Degrees for each layer's rotation
fiber_geometry = 'rect'  # Fiber shape type

overall_height = 2.0  # Height of the entire structure
plate_dimension = 2.0  # Each plate's width and length
layer_thickness = overall_height / num_layers  # Thickness of each layer
fiber_spacing = 0.01  # Space between fibers

def create_fiber(geometry, diameter, x_pos, y_pos, z_pos, thickness):
    if geometry == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        fiber_object = bpy.context.object
        fiber_object.dimensions = (thickness, diameter, plate_dimension)
        return fiber_object

def create_fiber_layer(layer_index):
    z_position = layer_index * layer_thickness
    current_rotation = layer_index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_diameter = layer_thickness
    spacing_between_fibers = fiber_diameter + fiber_spacing
    total_fibers = max(1, int(plate_dimension / spacing_between_fibers))

    total_space = total_fibers * spacing_between_fibers
    initial_y = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_space) / 2

    for i in range(total_fibers):
        fiber_y_position = initial_y + i * spacing_between_fibers
        fiber_instance = create_fiber(
            geometry=fiber_geometry,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_position,
            z_pos=z_position,
            thickness=layer_thickness
        )
        fiber_instance.parent = empty_layer
        fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

    empty_layer.rotation_euler[2] = math.radians(current_rotation)
    return empty_layer

for layer_idx in range(num_layers):
    create_fiber_layer(layer_idx)
