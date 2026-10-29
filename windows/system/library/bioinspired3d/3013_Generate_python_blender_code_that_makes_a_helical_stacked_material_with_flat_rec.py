# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_python_blender_code_that_makes_a_helical_stacked_material_with_flat_rec" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate python blender code that makes a helical stacked material with flat rectangular struts in each layer

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Total layers in the helical structure
angle_per_layer = 15  # Degrees of rotation for each layer
fiber_type = 'rect'

# Dimensions of the overall structure
structure_height = 2.0  # Height of the entire structure
plate_dimension = 2.0  # Size of each square plate
layer_thickness = structure_height / layers_count  # Thickness of each layer
fiber_spacing_distance = 0.01  # Gap between fibers

def create_fiber(fiber_type, diameter, x, y, z, thickness):
    if fiber_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, plate_dimension)
        return cube


def generate_layer(index):
    z_position = index * layer_thickness
    rotation_angle = index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    spacing = fiber_diameter + fiber_spacing_distance
    fiber_count = max(1, int(plate_dimension / spacing))

    total_fiber_space = fiber_count * spacing
    start_y_position = -plate_dimension / 2 + spacing / 2 + (plate_dimension - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_center_y = start_y_position + i * spacing
        fiber_instance = create_fiber(
            fiber_type=fiber_type,
            diameter=fiber_diameter,
            x=0,
            y=fiber_center_y,
            z=z_position,
            thickness=layer_thickness
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Build the entire structure
for i in range(layers_count):
    generate_layer(i)
