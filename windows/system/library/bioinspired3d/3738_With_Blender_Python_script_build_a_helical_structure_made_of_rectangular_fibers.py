# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_Blender_Python_script_build_a_helical_structure_made_of_rectangular_fibers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With Blender Python script build a helical structure made of rectangular fibers. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for helical fiber structure
layers_count = 10  # Number of layers in the structure
angle_per_layer = 15  # Rotation angle in degrees for each layer
fiber_type = 'rect'  # Type of fiber shape

# Overall dimensions of the structure
structure_height = 2  # Total height of the structure
plate_dimension = 2  # Width and length of each square plate
layer_thickness = structure_height / layers_count  # Thickness of each layer
fiber_spacing = 0.01  # Gap between fibers

def create_fiber(shape, diameter, x, y, z, thickness):
    if shape == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z), rotation=(0, math.radians(90), 0))
        fiber = bpy.context.object
        fiber.dimensions = (thickness, diameter, plate_dimension)
        return fiber

def build_layer(index):
    height_offset = index * layer_thickness
    rotation_angle = index * angle_per_layer

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_offset))
    layer_empty = bpy.context.object

    diameter = layer_thickness
    spacing = diameter + fiber_spacing
    total_fibers = max(1, int(plate_dimension / spacing))

    total_fiber_space = total_fibers * spacing
    start_y_position = -plate_dimension / 2 + spacing / 2 + (plate_dimension - total_fiber_space) / 2

    for i in range(total_fibers):
        fiber_y_position = start_y_position + i * spacing
        fiber_object = create_fiber(
            shape=fiber_type,
            diameter=diameter,
            x=0,
            y=fiber_y_position,
            z=height_offset,
            thickness=layer_thickness
        )
        fiber_object.parent = layer_empty
        fiber_object.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation_angle)
    return layer_empty

# Construct the entire structure
for i in range(layers_count):
    build_layer(i)
