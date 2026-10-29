# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_helical_Bouligand_material_where_each_ply_consists_of_rect" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a helical Bouligand material where each ply consists of rectangular fibers using blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber configuration
layer_quantity = 10  # Number of layers
rotation_degree = 15  # Degrees of rotation for each layer
fiber_form = 'rect'  # Shape of the fiber

# Structure dimensions
overall_height = 2  # Height of the entire structure
plate_length = 2  # Length of each plate
layer_height_thickness = overall_height / layer_quantity  # Thickness of each layer
fiber_spacing_distance = 0.01  # Space between fibers

def create_fiber_shape(form, diameter, x_pos, y_pos, z_pos, layer_thickness):
    if form == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_pos, y_pos, z_pos), rotation=(0, math.radians(90), 0))
        fiber_shape = bpy.context.object
        fiber_shape.dimensions = (layer_thickness, diameter, plate_length)
        return fiber_shape

def build_layer_structure(index):
    z_coord = index * layer_height_thickness
    rotation_angle = index * rotation_degree

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_coord))
    layer_empty = bpy.context.object

    fiber_diameter = layer_height_thickness
    fiber_gap = fiber_diameter + fiber_spacing_distance
    fiber_count = max(1, int(plate_length / fiber_gap))

    total_fiber_space = fiber_count * fiber_gap
    start_y_coord = -plate_length / 2 + fiber_gap / 2 + (plate_length - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_y_position = start_y_coord + i * fiber_gap
        fiber_instance = create_fiber_shape(
            form=fiber_form,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y_position,
            z_pos=z_coord,
            layer_thickness=layer_height_thickness
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Generate the helical structure
for i in range(layer_quantity):
    build_layer_structure(i)
