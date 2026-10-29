# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_creates_a_helical_Bouligand_bioinspired_material_with_cyli" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that creates a helical Bouligand bioinspired material with cylindrical rods forming each layer think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for helical fiber design
ply_count = 7  # Number of plies in the structure
rotation_step = 10  # Rotation angle for each ply
fiber_shape_type = 'cylinder'  # Shape of fibers

# Dimensions of the structure
entire_height = 2  # Total height
plate_dimension = 2  # Width and length of the plate
thickness_per_ply = entire_height / ply_count  # Thickness of each ply

# Function to generate a fiber
def generate_fiber(shape_type, diameter, x_coord, y_coord, z_coord):
    if shape_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_coord, y_coord, z_coord),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

# Function to create a single ply
def build_ply(ply_index):
    z_coord = ply_index * thickness_per_ply
    rotation_angle = ply_index * rotation_step

    # Create an empty object for the ply
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_coord))
    ply_empty = bpy.context.object

    fiber_diameter = thickness_per_ply
    fiber_quantity = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_length = fiber_quantity * fiber_diameter
    remaining_space = plate_dimension - total_fiber_length
    start_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_quantity):
        fiber_y_center = start_y + i * fiber_diameter
        fiber_instance = generate_fiber(
            shape_type=fiber_shape_type,
            diameter=fiber_diameter,
            x_coord=0,
            y_coord=fiber_y_center,
            z_coord=z_coord
        )
        fiber_instance.parent = ply_empty
        fiber_instance.location = (0, fiber_y_center, 0)

    # Rotate the empty object
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ply_empty
    ply_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return ply_empty

# Generate the structure
for i in range(ply_count):
    build_ply(i)
