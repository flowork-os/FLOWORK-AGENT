# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_that_creates_a_helical_Bouligand_material_with_flat_rectangular" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender that creates a helical Bouligand material with flat rectangular struts in each layer

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure parameters
ply_count = 12  # Number of plies in the structure
angle_step = 5  # Rotation angle for each ply in degrees
fiber_geometry = 'rect'  # Geometry of fibers

# Dimensions of the structure
height_total = 2  # Total height of the structure
plate_dim = 2  # Width and length of each square plate
thickness_per_ply = height_total / ply_count  # Thickness of each ply
fiber_spacing_distance = 0.01  # Distance between fibers


def create_fiber_shape(geometry, diameter, x_pos, y_pos, z_pos, thickness):
    if geometry == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, plate_dim)
        return cube


def assemble_layer(layer_num):
    # Assemble a helical layer of fibers

    z_position = layer_num * thickness_per_ply
    rotation_value = layer_num * angle_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_radius = thickness_per_ply
    fiber_distance = fiber_radius + fiber_spacing_distance
    fiber_count = max(1, int(plate_dim / fiber_distance))

    total_fiber_length = fiber_count * fiber_distance
    start_y = -plate_dim / 2 + fiber_distance / 2 + (plate_dim - total_fiber_length) / 2

    for i in range(fiber_count):
        fiber_y = start_y + i * fiber_distance
        fiber_instance = create_fiber_shape(
            geometry=fiber_geometry,
            diameter=fiber_radius,
            x_pos=0,
            y_pos=fiber_y,
            z_pos=z_position,
            thickness=thickness_per_ply
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_value)
    return layer_empty

# Generate the helical structure
for layer in range(ply_count):
    assemble_layer(layer)
