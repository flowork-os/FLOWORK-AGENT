# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_code_in_Blender_that_generates_a_model_of_a_helical_material_where_each_pl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write code in Blender that generates a model of a helical material where each ply consists of rectangular fibers.

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure settings
ply_count = 6
rotation_increment = 12
fiber_shape = 'rect'

# Overall dimensions
total_height = 2.0
plate_dimension = 2.0
layer_thickness = total_height / ply_count
fiber_gap = 0.01

# Function to create a fiber
def create_fiber(shape, diameter, x, y, z, thickness):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z), rotation=(0, math.radians(90), 0))
        fiber = bpy.context.object
        fiber.dimensions = (thickness, diameter, plate_dimension)
        return fiber

# Function to create a layer
def create_layer(index):
    z_position = index * layer_thickness
    rotation_angle = index * rotation_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    spacing = fiber_diameter + fiber_gap
    fiber_count = max(1, int(plate_dimension / spacing))

    total_fiber_length = fiber_count * spacing
    initial_y_position = -plate_dimension / 2 + spacing / 2 + (plate_dimension - total_fiber_length) / 2

    for i in range(fiber_count):
        fiber_y_position = initial_y_position + i * spacing
        fiber_instance = create_fiber(fiber_shape, fiber_diameter, 0, fiber_y_position, z_position, layer_thickness)
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Generate the helical structure
for i in range(ply_count):
    create_layer(i)
