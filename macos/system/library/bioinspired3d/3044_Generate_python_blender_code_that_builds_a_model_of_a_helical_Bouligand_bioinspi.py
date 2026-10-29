# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_python_blender_code_that_builds_a_model_of_a_helical_Bouligand_bioinspi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate python blender code that builds a model of a helical Bouligand bioinspired structure with flat rectangular struts in each layer

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the fiber layers
ply_count = 8  # Number of layers in the structure
rotation_angle = 10  # Angle of rotation for each layer
fiber_geometry = 'rectangle'  # Fiber shape type

# Structure dimensions
structure_height = 2  # Total height of the structure
plate_dim = 2  # Width and length of each square plate
thickness_per_layer = structure_height / ply_count  # Thickness of each layer
fiber_gap_distance = 0.01  # Distance between fibers


def add_fiber_shape(shape, diameter, x, y, z, thickness):
    if shape == 'rectangle':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        fiber_cube = bpy.context.object
        fiber_cube.dimensions = (thickness, diameter, plate_dim)
        return fiber_cube


def construct_layer(layer_idx):
    # Constructs a helical layer of fibers.

    z_pos = layer_idx * thickness_per_layer
    rotation_for_layer = layer_idx * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_pos))
    layer_empty_object = bpy.context.object

    fiber_diameter = thickness_per_layer
    fiber_spacing = fiber_diameter + fiber_gap_distance
    fiber_count = max(1, int(plate_dim / fiber_spacing))

    total_fiber_area = fiber_count * fiber_spacing
    start_y_coord = -plate_dim / 2 + fiber_spacing / 2 + (plate_dim - total_fiber_area) / 2

    for j in range(fiber_count):
        fiber_y_position = start_y_coord + j * fiber_spacing
        fiber_instance = add_fiber_shape(
            shape=fiber_geometry,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y_position,
            z=z_pos,
            thickness=thickness_per_layer
        )
        fiber_instance.parent = layer_empty_object
        fiber_instance.matrix_parent_inverse = layer_empty_object.matrix_world.inverted()

    layer_empty_object.rotation_euler[2] = math.radians(rotation_for_layer)
    return layer_empty_object

# Build the entire structure
for k in range(0, ply_count):
    construct_layer(k)
