# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_a_helical_bioinspired_structure_with_flat_rectangular_strut" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of a helical bioinspired structure with flat rectangular struts in each layer using a blender code think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure settings
total_layers = 12  # Total number of layers
angle_increment = 5  # Degree rotation per layer
fiber_form = 'rect'  # Fiber form used

# Dimensions of the overall structure
full_height = 2.0  # Total height of the structure
plate_dimension = 2.0  # Size of each square plate
layer_thickness = full_height / total_layers  # Thickness of each layer
fiber_spacing = 0.01  # Space between fibers

# Function to add a fiber
def create_fiber(form, diameter, x_coord, y_coord, z_coord, thickness):
    if form == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_coord, y_coord, z_coord), rotation=(0, math.radians(90), 0))
        fiber_obj = bpy.context.object
        fiber_obj.dimensions = (thickness, diameter, plate_dimension)
        return fiber_obj

# Function to create a layer
def construct_layer(layer_num):
    z_position = layer_num * layer_thickness
    rotation_angle = layer_num * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    spacing = fiber_diameter + fiber_spacing
    fiber_count = max(1, int(plate_dimension / spacing))

    total_fiber_length = fiber_count * spacing
    start_y = -plate_dimension / 2 + spacing / 2 + (plate_dimension - total_fiber_length) / 2

    for i in range(fiber_count):
        fiber_y_position = start_y + i * spacing
        fiber_instance = create_fiber(
            form=fiber_form,
            diameter=fiber_diameter,
            x_coord=0,
            y_coord=fiber_y_position,
            z_coord=z_position,
            thickness=layer_thickness
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Generate the helical structure
for i in range(total_layers):
    construct_layer(i)
