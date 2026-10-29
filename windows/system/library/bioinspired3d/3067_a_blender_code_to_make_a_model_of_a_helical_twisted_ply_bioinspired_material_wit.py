# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_to_make_a_model_of_a_helical_twisted_ply_bioinspired_material_wit" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code to make a model of a helical twisted ply bioinspired material with each layer formed by rectangular fibers

import bpy
import math

# Clear the scene of existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber structure
ply_count = 9  # Number of plies in the structure
rotation_per_ply = 12  # Degrees of rotation per ply
fiber_shape = 'rect'  # Shape of fibers

# Define overall dimensions
structure_height = 2.0
plate_size = 2.0
ply_thickness = structure_height / ply_count  # Thickness of each ply
fiber_gap = 0.01  # Gap between fibers

# Function to create a fiber
def add_fiber(shape_type, diameter, x, y, z, thickness):
    if shape_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        fiber_object = bpy.context.object
        fiber_object.dimensions = (thickness, diameter, plate_size)
        return fiber_object

# Function to create a ply
def create_ply(index):
    z_pos = index * ply_thickness
    rotation_angle = index * rotation_per_ply

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_pos))
    ply_empty = bpy.context.object

    fiber_diameter = ply_thickness
    fiber_distance = fiber_diameter + fiber_gap
    total_fibers = max(1, int(plate_size / fiber_distance))

    total_space = total_fibers * fiber_distance
    start_y = -plate_size / 2 + fiber_distance / 2 + (plate_size - total_space) / 2

    for i in range(total_fibers):
        fiber_center_y = start_y + i * fiber_distance
        fiber_instance = add_fiber(
            shape_type=fiber_shape,
            diameter=fiber_diameter,
            x=0,
            y=fiber_center_y,
            z=z_pos,
            thickness=ply_thickness
        )
        fiber_instance.parent = ply_empty
        fiber_instance.matrix_parent_inverse = ply_empty.matrix_world.inverted()

    ply_empty.rotation_euler[2] = math.radians(rotation_angle)
    return ply_empty

# Create the structure
for i in range(ply_count):
    create_ply(i)
