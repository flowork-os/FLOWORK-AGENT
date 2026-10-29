# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_blender_script_that_constructs_a_model_of_a_helical_twisted_ply_bioinspired" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make blender script that constructs a model of a helical twisted ply bioinspired structure where each ply consists of rectangular fibers

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
ply_count = 12  # Total number of plies
rotation_angle = 15  # Rotation per ply
fiber_shape = 'rect'  # Fiber shape

# Dimensions of the structure
structure_height = 2.0
plate_dimension = 2.0
ply_thickness = structure_height / ply_count  # Thickness of each ply
fiber_spacing = 0.01  # Gap between fibers

# Function to create a fiber
def create_fiber(shape_type, diameter, x, y, z, thickness):
    if shape_type == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        fiber = bpy.context.object
        fiber.dimensions = (thickness, diameter, plate_dimension)
        return fiber

# Function to create a single ply
def create_ply(index):
    z_pos = index * ply_thickness
    rotation_offset = index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_pos))
    ply_empty = bpy.context.object

    fiber_diameter = ply_thickness
    spacing = fiber_diameter + fiber_spacing
    total_fibers = max(1, int(plate_dimension / spacing))

    total_space = total_fibers * spacing
    start_y = -plate_dimension / 2 + spacing / 2 + (plate_dimension - total_space) / 2

    for i in range(total_fibers):
        fiber_y = start_y + i * spacing
        fiber_instance = create_fiber(
            shape_type=fiber_shape,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y,
            z=z_pos,
            thickness=ply_thickness
        )
        fiber_instance.parent = ply_empty
        fiber_instance.matrix_parent_inverse = ply_empty.matrix_world.inverted()

    ply_empty.rotation_euler[2] = math.radians(rotation_offset)
    return ply_empty

# Generate the complete structure
for i in range(ply_count):
    create_ply(i)
