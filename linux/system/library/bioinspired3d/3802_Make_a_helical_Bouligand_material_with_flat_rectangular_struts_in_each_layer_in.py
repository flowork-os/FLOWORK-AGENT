# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_helical_Bouligand_material_with_flat_rectangular_struts_in_each_layer_in" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a helical Bouligand material with flat rectangular struts in each layer in blender python code Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
ply_total = 10
rotation_step = 15
fiber_shape_type = 'rect'

# Structure dimensions
full_height = 2.0
plate_side = 2.0
individual_thickness = full_height / ply_total
fiber_gap_size = 0.01

def insert_fiber(shape_type, diameter, x_coord, y_coord, z_coord, thickness):
    if shape_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_coord, y_coord, z_coord), rotation=(0, math.radians(90), 0))
        fiber_cube = bpy.context.object
        fiber_cube.dimensions = (thickness, diameter, plate_side)
        return fiber_cube

def build_fiber_layer(layer_index):
    height_position = layer_index * individual_thickness
    current_rotation = layer_index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_position))
    layer_empty_object = bpy.context.object

    fiber_diameter = individual_thickness
    fiber_spacing = fiber_diameter + fiber_gap_size
    fiber_count = max(1, int(plate_side / fiber_spacing))

    total_fiber_area = fiber_count * fiber_spacing
    initial_y_position = -plate_side / 2 + fiber_spacing / 2 + (plate_side - total_fiber_area) / 2

    for i in range(fiber_count):
        fiber_y_position = initial_y_position + i * fiber_spacing
        fiber_object = insert_fiber(fiber_shape_type, fiber_diameter, 0, fiber_y_position, height_position, individual_thickness)
        fiber_object.parent = layer_empty_object
        fiber_object.matrix_parent_inverse = layer_empty_object.matrix_world.inverted()

    layer_empty_object.rotation_euler[2] = math.radians(current_rotation)
    return layer_empty_object

# Construct the helical structure
for index in range(ply_total):
    build_fiber_layer(index)
