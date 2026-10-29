# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_a_helical_twisted_ply_structure_with_flat_rectangular_struts" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of a helical twisted ply structure with flat rectangular struts in each layer in blender python code think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for fiber structure
layers = 14  # Number of layers
rotation_step = 3  # Degrees of rotation per layer
fiber_form = 'rect'  # Type of fiber

# Dimensions of the structure
structure_height = 2.0  # Total height
plate_size = 2.0  # Size of each plate
layer_thickness = structure_height / layers  # Thickness of each layer
fiber_spacing = 0.01  # Space between fibers

def create_fiber(form, diameter, x_pos, y_pos, z_pos, thickness):
    if form == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_pos, y_pos, z_pos), rotation=(0, math.radians(90), 0))
        fiber_object = bpy.context.object
        fiber_object.dimensions = (thickness, diameter, plate_size)
        return fiber_object

def construct_layer(index):
    z_position = index * layer_thickness
    rotation_angle = index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    spacing_between_fibers = fiber_diameter + fiber_spacing
    fiber_count = max(1, int(plate_size / spacing_between_fibers))

    total_spacing = fiber_count * spacing_between_fibers
    start_y = -plate_size / 2 + spacing_between_fibers / 2 + (plate_size - total_spacing) / 2

    for i in range(fiber_count):
        fiber_y_center = start_y + i * spacing_between_fibers
        fiber_instance = create_fiber(fiber_form, fiber_diameter, 0, fiber_y_center, z_position, layer_thickness)
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Build the structure
for idx in range(layers):
    construct_layer(idx)
