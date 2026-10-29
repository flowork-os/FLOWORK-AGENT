# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_helical_twisted_ply_structure_with_each_layer_formed_by_rectangular" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a helical twisted ply structure with each layer formed by rectangular fibers using blender python code Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

ply_count = 8  # Number of plies in the helical arrangement
angle_per_ply = 4  # Degrees of rotation for each ply
fiber_shape_type = 'rect'  # Shape of fibers

complete_height = 2.0  # Total height of the structure
plate_dimension = 2.0  # Dimensions of each square plate
ply_thickness = complete_height / ply_count  # Thickness of each ply
fiber_gap = 0.01  # Gap between fibers

def add_fiber(shape, diameter, x, y, z, thickness):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        fiber_object = bpy.context.object
        fiber_object.dimensions = (thickness, diameter, plate_dimension)
        return fiber_object

def create_ply(index):
    z_height = index * ply_thickness
    rotation_angle = index * angle_per_ply

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_height))
    empty_ply = bpy.context.object

    fiber_diameter = ply_thickness
    fiber_spacing = fiber_diameter + fiber_gap
    total_fibers = max(1, int(plate_dimension / fiber_spacing))

    total_space = total_fibers * fiber_spacing
    start_y = -plate_dimension / 2 + fiber_spacing / 2 + (plate_dimension - total_space) / 2

    for i in range(total_fibers):
        fiber_center_y = start_y + i * fiber_spacing
        fiber_instance = add_fiber(
            shape=fiber_shape_type,
            diameter=fiber_diameter,
            x=0,
            y=fiber_center_y,
            z=z_height,
            thickness=ply_thickness
        )
        fiber_instance.parent = empty_ply
        fiber_instance.matrix_parent_inverse = empty_ply.matrix_world.inverted()

    empty_ply.rotation_euler[2] = math.radians(rotation_angle)
    return empty_ply

for i in range(ply_count):
    create_ply(i)
