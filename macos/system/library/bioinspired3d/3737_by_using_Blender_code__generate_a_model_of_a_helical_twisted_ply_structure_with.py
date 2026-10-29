# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_Blender_code__generate_a_model_of_a_helical_twisted_ply_structure_with" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using Blender code, generate a model of a helical twisted ply structure with flat rectangular struts in each layer. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
plys = 6  # Number of plies in the structure
rotation_per_ply_angle = 8  # Rotation angle in degrees for each ply
fiber_form_type = "rect"  # Type of fiber

# Dimensions of the overall structure
complete_height = 2  # Total height of the structure
each_plate_size = 2  # Size of each square plate
thickness_of_each_ply = complete_height / plys  # Thickness of each ply
fiber_gap_space = 0.01  # Small gap between fibers

def create_fiber_shape(form_type, diameter, x_pos, y_pos, z_pos, thickness):
    if form_type == "rect":
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, each_plate_size)
        return cube

def build_helical_ply(index):
    z_height = index * thickness_of_each_ply
    base_rotation = index * rotation_per_ply_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_height))
    empty_object = bpy.context.object

    fiber_diameter = thickness_of_each_ply
    fiber_spacing = fiber_diameter + fiber_gap_space
    fiber_count = max(1, int(each_plate_size / fiber_spacing))

    total_space = fiber_count * fiber_spacing
    start_y_pos = -each_plate_size / 2 + fiber_spacing / 2 + (each_plate_size - total_space) / 2

    for i in range(fiber_count):
        fiber_center_y = start_y_pos + i * fiber_spacing
        fiber_instance = create_fiber_shape(
            form_type=fiber_form_type,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_center_y,
            z_pos=z_height,
            thickness=thickness_of_each_ply
        )
        fiber_instance.parent = empty_object
        fiber_instance.matrix_parent_inverse = empty_object.matrix_world.inverted()

    empty_object.rotation_euler[2] = math.radians(base_rotation)
    return empty_object

# Create the helical structure
for i in range(plys):
    build_helical_ply(i)
