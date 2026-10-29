# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_script_create_a_helical_twisted_ply_bioinspired_material_wher" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender script create a helical twisted ply bioinspired material where each ply consists of rectangular fibers

import bpy
import math

# Clear the scene before creation
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for helical fiber assembly
ply_count = 6  # Number of plies in the model
rotation_angle = 15  # Rotation in degrees for each ply
fiber_style = 'rect'

# Overall dimensions of the structure
structure_height = 2.0  # Height of the structure
plate_dimension = 2.0  # Size of each plate
ply_thickness = structure_height / ply_count  # Thickness of each ply
fiber_gap = 0.01  # Space between fibers


def create_fiber(shape, diameter, x, y, z, thickness):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        cube = bpy.context.object
        cube.dimensions = (thickness, diameter, plate_dimension)
        return cube


def generate_helical_plate(index):
    # Function to create a helical plate
    z_position = index * ply_thickness
    rotation_value = index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_plate = bpy.context.object

    fiber_diameter = ply_thickness
    spacing = fiber_diameter + fiber_gap
    fiber_count = max(1, int(plate_dimension / spacing))

    total_space = fiber_count * spacing
    start_y = -plate_dimension / 2 + spacing / 2 + (plate_dimension - total_space) / 2

    for i in range(fiber_count):
        fiber_center_y = start_y + i * spacing
        fiber_object = create_fiber(
            shape=fiber_style,
            diameter=fiber_diameter,
            x=0,
            y=fiber_center_y,
            z=z_position,
            thickness=ply_thickness
        )
        fiber_object.parent = empty_plate
        fiber_object.matrix_parent_inverse = empty_plate.matrix_world.inverted()

    empty_plate.rotation_euler[2] = math.radians(rotation_value)
    return empty_plate

# Create the structure
for i in range(ply_count):
    generate_helical_plate(i)
