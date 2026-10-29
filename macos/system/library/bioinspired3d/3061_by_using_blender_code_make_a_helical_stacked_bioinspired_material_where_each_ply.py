# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_code_make_a_helical_stacked_bioinspired_material_where_each_ply" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender code make a helical stacked bioinspired material where each ply consists of rectangular fibers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure definition
layer_total = 15
rotation_angle = 20
fiber_shape = 'rect'

# Structure dimensions
helical_height = 2
plate_dimension = 2
layer_thickness = helical_height / layer_total
fiber_spacing = 0.01

class HelicalFiber:
    @staticmethod
    def create_fiber(fiber_shape, diameter, location, thickness):
        if fiber_shape == 'rect':
            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                location=location,
                rotation=(0, math.radians(90), 0)
            )
            fiber = bpy.context.object
            fiber.dimensions = (thickness, diameter, plate_dimension)
            return fiber

def create_layer(layer_index):
    height_position = layer_index * layer_thickness
    rotation_position = layer_index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_count = max(1, int(plate_dimension / (fiber_diameter + fiber_spacing)))

    total_length = fiber_count * (fiber_diameter + fiber_spacing)
    start_y = -plate_dimension / 2 + (fiber_spacing / 2) + (plate_dimension - total_length) / 2

    for i in range(fiber_count):
        fiber_y = start_y + i * (fiber_diameter + fiber_spacing)
        fiber_instance = HelicalFiber.create_fiber(
            fiber_shape=fiber_shape,
            diameter=fiber_diameter,
            location=(0, fiber_y, height_position),
            thickness=layer_thickness
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_position)
    return layer_empty

# Build the helical structure
for i in range(layer_total):
    create_layer(i)
