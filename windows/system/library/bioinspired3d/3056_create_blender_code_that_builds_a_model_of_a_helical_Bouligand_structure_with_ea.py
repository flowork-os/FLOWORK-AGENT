# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_blender_code_that_builds_a_model_of_a_helical_Bouligand_structure_with_ea" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create blender code that builds a model of a helical Bouligand structure with each layer formed by rectangular fibers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber design
ply_count = 8  # Number of plies in the design
angle_increment = 3  # Degrees of rotation per ply
fiber_shape = "rect"

# Overall structure dimensions
structure_height = 2  # Total height of the structure
plate_size = 2  # Width and length of each plate
ply_height = structure_height / ply_count  # Height of each ply
fiber_gap = 0.01  # Gap between fibers

def add_fiber(fiber_shape, fiber_diameter, x, y, z, height):
    if fiber_shape == "rect":
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (height, fiber_diameter, plate_size)
        return cube

def create_ply(index):
    # Function to create a ply of fibers in a helical arrangement.

    z_position = index * ply_height
    rotation_angle = index * angle_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    ply_empty = bpy.context.object

    fiber_diameter = ply_height
    spacing_between_fibers = fiber_diameter + fiber_gap
    total_fibers = max(1, int(plate_size / spacing_between_fibers))

    total_space_needed = total_fibers * spacing_between_fibers
    start_y_position = -plate_size / 2 + spacing_between_fibers / 2 + (plate_size - total_space_needed) / 2

    for i in range(total_fibers):
        fiber_y_position = start_y_position + i * spacing_between_fibers
        fiber_instance = add_fiber(
            fiber_shape=fiber_shape,
            fiber_diameter=fiber_diameter,
            x=0,
            y=fiber_y_position,
            z=z_position,
            height=ply_height
        )
        fiber_instance.parent = ply_empty
        fiber_instance.matrix_parent_inverse = ply_empty.matrix_world.inverted()

    ply_empty.rotation_euler[2] = math.radians(rotation_angle)
    return ply_empty

# Generate the helical structure
for i in range(ply_count):
    create_ply(i)
