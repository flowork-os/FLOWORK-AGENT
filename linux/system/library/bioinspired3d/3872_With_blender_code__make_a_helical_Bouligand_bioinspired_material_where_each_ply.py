# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_code__make_a_helical_Bouligand_bioinspired_material_where_each_ply" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender code, make a helical Bouligand bioinspired material where each ply consists of cylindrical fibers. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for creating a helical structure
ply_count = 15  # Number of plies in the structure
rotation_step = 3  # Degrees of rotation for each ply
fiber_shape_type = 'cylinder'  # Shape of fibers

# Structure dimensions
height_of_structure = 2  # Total height
plate_side_length = 2  # Length of each square plate
thickness_of_ply = height_of_structure / ply_count  # Thickness of each ply

def generate_fiber(shape_type, diameter, x_coord, y_coord, z_coord):
    if shape_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_side_length,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def create_helical_ply(index):
    z_position = index * thickness_of_ply
    rotation_angle = index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_object = bpy.context.object

    fiber_diameter = thickness_of_ply
    count_of_fibers = max(1, int(plate_side_length / fiber_diameter))

    total_fiber_area = count_of_fibers * fiber_diameter
    remaining_area = plate_side_length - total_fiber_area
    initial_y_coord = -plate_side_length / 2 + (fiber_diameter / 2) + (remaining_area / 2)

    for i in range(count_of_fibers):
        fiber_y_coord = initial_y_coord + i * fiber_diameter
        fiber_instance = generate_fiber(
            shape_type=fiber_shape_type,
            diameter=fiber_diameter,
            x_coord=0,
            y_coord=fiber_y_coord,
            z_coord=z_position
        )
        fiber_instance.parent = empty_object
        fiber_instance.location = (0, fiber_y_coord, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_object
    empty_object.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return empty_object

# Generate the helical structure
for i in range(ply_count):
    create_helical_ply(i)
