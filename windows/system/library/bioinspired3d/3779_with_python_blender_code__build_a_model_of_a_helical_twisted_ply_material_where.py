# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_python_blender_code__build_a_model_of_a_helical_twisted_ply_material_where" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with python blender code, build a model of a helical twisted ply material where each ply consists of rectangular fibers think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 7
rotation_angle = 15
fiber_shape_type = 'rect'

height_of_structure = 2.0
size_of_plate = 2.0
thickness_of_layer = height_of_structure / num_layers
gap_between_fibers = 0.01

def create_fiber(shape, diameter, x, y, z, thickness):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z), rotation=(0, math.radians(90), 0))
        fiber = bpy.context.object
        fiber.dimensions = (thickness, diameter, size_of_plate)
        return fiber

def create_layer(layer_index):
    z_position = layer_index * thickness_of_layer
    rotation_for_layer = layer_index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = thickness_of_layer
    fiber_spacing = fiber_diameter + gap_between_fibers
    fibers_count = max(1, int(size_of_plate / fiber_spacing))

    total_fiber_length = fibers_count * fiber_spacing
    initial_y_position = -size_of_plate / 2 + fiber_spacing / 2 + (size_of_plate - total_fiber_length) / 2

    for i in range(fibers_count):
        fiber_y_position = initial_y_position + i * fiber_spacing
        fiber_object = create_fiber(shape=fiber_shape_type, diameter=fiber_diameter, x=0, y=fiber_y_position, z=z_position, thickness=thickness_of_layer)
        fiber_object.parent = layer_empty
        fiber_object.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_for_layer)
    return layer_empty

for i in range(num_layers):
    create_layer(i)
