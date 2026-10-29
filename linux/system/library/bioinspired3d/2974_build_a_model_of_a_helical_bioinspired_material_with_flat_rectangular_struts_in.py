# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_a_helical_bioinspired_material_with_flat_rectangular_struts_in" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of a helical bioinspired material with flat rectangular struts in each layer using Blender code

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber assembly
ply_count = 7  # Number of plies in the structure
rotation_step = 10  # Rotation increment for each ply
fiber_type = 'rect'  # Fiber shape

# Overall dimensions
structure_height = 2.0  # Height of the structure
plate_size = 2.0  # Size of each plate
ply_height = structure_height / ply_count  # Height of each ply
fiber_gap = 0.01  # Gap between fibers

# Function to create a fiber
def create_fiber(type, diameter, x, y, z, height):
    if type == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        fiber = bpy.context.object
        fiber.dimensions = (height, diameter, plate_size)
        return fiber

# Function to generate a single ply
def generate_ply(ply_index):
    z_position = ply_index * ply_height
    rotation_angle = ply_index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    ply_empty = bpy.context.object

    fiber_diameter = ply_height
    spacing = fiber_diameter + fiber_gap
    fiber_count = max(1, int(plate_size / spacing))

    total_fiber_space = fiber_count * spacing
    start_y = -plate_size / 2 + spacing / 2 + (plate_size - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_y = start_y + i * spacing
        fiber_instance = create_fiber(
            type=fiber_type,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y,
            z=z_position,
            height=ply_height
        )
        fiber_instance.parent = ply_empty
        fiber_instance.matrix_parent_inverse = ply_empty.matrix_world.inverted()

    ply_empty.rotation_euler[2] = math.radians(rotation_angle)
    return ply_empty

# Construct the entire structure
for i in range(ply_count):
    generate_ply(i)
