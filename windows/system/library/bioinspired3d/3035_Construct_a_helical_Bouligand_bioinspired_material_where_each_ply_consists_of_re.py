# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_helical_Bouligand_bioinspired_material_where_each_ply_consists_of_re" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a helical Bouligand bioinspired material where each ply consists of rectangular fibers using a Blender code

import bpy
import math

# Remove all existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Fiber structure parameters
ply_count = 12
angle_increment = 20
fiber_shape_type = "rect"

# Structure dimensions
structure_height = 2
plate_dimension = 2
layer_thickness = structure_height / ply_count
fiber_gap = 0.01

def create_fiber_object(shape_type, fiber_radius, x_pos, y_pos, z_pos):
    if shape_type == "rect":
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_pos, y_pos, z_pos), rotation=(0, math.radians(90), 0))
        fiber_cube = bpy.context.object
        fiber_cube.dimensions = (layer_thickness, fiber_radius, plate_dimension)
        return fiber_cube


def build_helical_structure():
    for layer_index in range(ply_count):
        z_position = layer_index * layer_thickness
        rotation_angle = layer_index * angle_increment

        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
        empty_layer = bpy.context.object

        fiber_radius = layer_thickness
        fiber_distance = fiber_radius + fiber_gap
        fiber_count = max(1, int(plate_dimension / fiber_distance))

        total_fiber_space = fiber_count * fiber_distance
        start_y_position = -plate_dimension / 2 + fiber_distance / 2 + (plate_dimension - total_fiber_space) / 2

        for i in range(fiber_count):
            fiber_y_center = start_y_position + i * fiber_distance
            fiber_instance = create_fiber_object(
                shape_type=fiber_shape_type,
                fiber_radius=fiber_radius,
                x_pos=0,
                y_pos=fiber_y_center,
                z_pos=z_position
            )
            fiber_instance.parent = empty_layer
            fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

        empty_layer.rotation_euler[2] = math.radians(rotation_angle)

# Execute the construction of the helical structure
build_helical_structure()
