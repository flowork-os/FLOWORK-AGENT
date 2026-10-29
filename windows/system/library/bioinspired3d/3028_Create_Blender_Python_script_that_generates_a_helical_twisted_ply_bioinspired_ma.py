# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_Blender_Python_script_that_generates_a_helical_twisted_ply_bioinspired_ma" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create Blender Python script that generates a helical twisted ply bioinspired material made of rectangular fibers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Number of layers in the structure
angle_per_layer = 15  # Rotation angle in degrees for each layer
fiber_type = 'rectangular'  # Type of fibers used

# Dimensions for the overall structure
structure_height = 2.0  # Total height of the structure
plate_dimension = 2.0  # Width and length of each square plate
layer_thickness = structure_height / layers_count  # Thickness of each layer
fiber_spacing = 0.01  # Gap between fibers

def create_fiber(fiber_type, diameter, pos_x, pos_y, pos_z, thickness):
    if fiber_type == 'rectangular':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(pos_x, pos_y, pos_z), rotation=(0, math.radians(90), 0))
        fiber = bpy.context.object
        fiber.dimensions = (thickness, diameter, plate_dimension)
        return fiber

def build_layer(layer_index):
    # Constructs a helical layer of fibers.
    height_position = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    spacing_between_fibers = fiber_diameter + fiber_spacing
    fibers_count = max(1, int(plate_dimension / spacing_between_fibers))

    total_fiber_space = fibers_count * spacing_between_fibers
    initial_y = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_fiber_space) / 2

    for i in range(fibers_count):
        fiber_y_position = initial_y + i * spacing_between_fibers
        fiber_instance = create_fiber(
            fiber_type=fiber_type,
            diameter=fiber_diameter,
            pos_x=0,
            pos_y=fiber_y_position,
            pos_z=height_position,
            thickness=layer_thickness
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Generate the full structure
for i in range(layers_count):
    build_layer(i)
