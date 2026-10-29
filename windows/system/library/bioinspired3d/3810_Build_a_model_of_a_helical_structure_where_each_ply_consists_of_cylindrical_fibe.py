# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_a_helical_structure_where_each_ply_consists_of_cylindrical_fibe" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of a helical structure where each ply consists of cylindrical fibers using a Blender script Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the helical fiber structure parameters
layer_count = 12  # Number of layers
rotation_increment = 5  # Rotation increment in degrees
fiber_geometry = 'cylinder'  # Fiber geometry type

# Dimensions of the structure
structure_height = 2  # Full height of the structure
plate_dimension = 2  # Dimension of the plates
layer_depth = structure_height / layer_count  # Depth of each layer

# Function to create fibers
def create_fiber(geometry, diameter, x_pos, y_pos, z_pos):
    if geometry == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

# Function to create a single layer of fibers
def construct_layer(index):
    z_coord = index * layer_depth
    rotation_angle = index * rotation_increment

    # Create an empty object to hold the fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_coord))
    layer_empty = bpy.context.object

    fiber_radius = layer_depth
    total_fibers = max(1, int(plate_dimension / fiber_radius))

    total_fiber_space = total_fibers * fiber_radius
    remaining_space = plate_dimension - total_fiber_space
    start_y_coord = -plate_dimension / 2 + (fiber_radius / 2) + (remaining_space / 2)

    for i in range(total_fibers):
        fiber_y_coord = start_y_coord + i * fiber_radius
        fiber_instance = create_fiber(
            geometry=fiber_geometry,
            diameter=fiber_radius,
            x_pos=0,
            y_pos=fiber_y_coord,
            z_pos=z_coord
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_y_coord, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

# Generate the entire structure
for i in range(layer_count):
    construct_layer(i)
