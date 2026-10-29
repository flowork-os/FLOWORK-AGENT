# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_Blender_code_that_makes_a_model_of_a_helical_Bouligand_material_where_eac" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create Blender code that makes a model of a helical Bouligand material where each ply consists of rectangular fibers.

import bpy
import math

# Clear existing objects in the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber assembly
layers = 11  # Number of layers in the helical structure
rotation_angle = 15  # Degrees of rotation for each layer
fiber_shape = 'rect'  # Shape of fibers

# Dimensions of the entire structure
height = 2.0  # Total height of the structure
size_of_plate = 2.0  # Size of each plate
thickness_of_layer = height / layers  # Thickness of each layer
fiber_spacing = 0.01  # Gap between fibers

# Function to add a fiber
def add_fiber(shape, diameter, x_pos, y_pos, z_pos, thickness):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x_pos, y_pos, z_pos),
            rotation=(0, math.radians(90), 0)
        )
        fiber = bpy.context.object
        fiber.dimensions = (thickness, diameter, size_of_plate)
        return fiber

# Function to create a layer
def create_layer(index):
    z_position = index * thickness_of_layer
    angle = index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = thickness_of_layer
    fiber_count = max(1, int(size_of_plate / (fiber_diameter + fiber_spacing)))

    total_fiber_space = fiber_count * (fiber_diameter + fiber_spacing)
    start_y = -size_of_plate / 2 + (fiber_diameter + fiber_spacing) / 2 + (size_of_plate - total_fiber_space) / 2

    for i in range(fiber_count):
        fiber_y = start_y + i * (fiber_diameter + fiber_spacing)
        fiber_instance = add_fiber(
            shape=fiber_shape,
            diameter=fiber_diameter,
            x_pos=0,
            y_pos=fiber_y,
            z_pos=z_position,
            thickness=thickness_of_layer
        )
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(angle)
    return layer_empty

# Build the helical structure
for i in range(layers):
    create_layer(i)
