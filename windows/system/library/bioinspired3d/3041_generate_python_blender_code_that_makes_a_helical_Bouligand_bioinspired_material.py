# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_python_blender_code_that_makes_a_helical_Bouligand_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate python blender code that makes a helical Bouligand bioinspired material made of rectangular fibers.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
ply_count = 9  # Total number of plies
rotation_step = 20  # Rotation in degrees for each ply
fiber_geom = "rect"

# Structure dimensions
height_total = 2
square_size = 2
thickness_per_ply = height_total / ply_count  # Thickness of each ply
fiber_distance = 0.01  # Distance between fibers

def insert_fiber(geometry, diameter, x_pos, y_pos, z_pos, thickness):
    if geometry == "rect":
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        fiber_object = bpy.context.object
        fiber_object.dimensions = (thickness, diameter, square_size)
        return fiber_object

def make_ply(ply_index):
    # Constructs a ply of fibers in a helical arrangement.
    z_position = ply_index * thickness_per_ply
    base_rotation = ply_index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    ply_empty = bpy.context.object

    fiber_diameter = thickness_per_ply
    spacing_between_fibers = fiber_diameter + fiber_distance
    total_fiber_count = max(1, int(square_size / spacing_between_fibers))

    total_spacing = total_fiber_count * spacing_between_fibers
    start_y_position = -square_size / 2 + spacing_between_fibers / 2 + (square_size - total_spacing) / 2

    for i in range(total_fiber_count):
        fiber_center_y = start_y_position + i * spacing_between_fibers
        fiber_instance = insert_fiber(
            geometry=fiber_geom,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_center_y,
            z_pos=z_position,
            thickness=thickness_per_ply
        )
        fiber_instance.parent = ply_empty
        fiber_instance.matrix_parent_inverse = ply_empty.matrix_world.inverted()

    ply_empty.rotation_euler[2] = math.radians(base_rotation)
    return ply_empty

# Create the helical structure
for i in range(ply_count):
    make_ply(i)
