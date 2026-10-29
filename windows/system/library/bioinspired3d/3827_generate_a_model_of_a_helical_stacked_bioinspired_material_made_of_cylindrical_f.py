# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_a_helical_stacked_bioinspired_material_made_of_cylindrical_f" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of a helical stacked bioinspired material made of cylindrical fibers in a Blender code think step by step.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
ply_count = 9  # Number of plies in the structure
angle_per_ply = 12  # Degrees of rotation for each ply
fiber_form = 'cylinder'  # Shape of the fibers

# Dimensions of the overall structure
height_of_structure = 2  # Total height of the structure
plate_dim = 2  # Width and length of each square plate
thickness_of_ply = height_of_structure / ply_count  # Thickness of each ply

# Function to create a fiber
def add_fiber(form, diameter, x, y, z):
    if form == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dim,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

# Function to generate a ply
def create_ply(index):
    z_position = index * thickness_of_ply
    rotation_angle = index * angle_per_ply

    # Create an empty object to group fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    ply_empty = bpy.context.object

    fiber_diameter = thickness_of_ply
    fiber_count = max(1, int(plate_dim / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    leftover_space = plate_dim - total_fiber_space
    start_y = -plate_dim / 2 + (fiber_diameter / 2) + (leftover_space / 2)

    for i in range(fiber_count):
        fiber_center_y = start_y + i * fiber_diameter
        fiber_instance = add_fiber(
            form=fiber_form,
            diameter=fiber_diameter,
            x=0,
            y=fiber_center_y,
            z=z_position
        )
        fiber_instance.parent = ply_empty
        fiber_instance.location = (0, fiber_center_y, 0)

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
    create_ply(i)
