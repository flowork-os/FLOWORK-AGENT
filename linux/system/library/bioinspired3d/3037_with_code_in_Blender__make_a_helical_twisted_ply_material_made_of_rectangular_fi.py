# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_code_in_Blender__make_a_helical_twisted_ply_material_made_of_rectangular_fi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with code in Blender, make a helical twisted ply material made of rectangular fibers.

import bpy
import math

# Clear the scene of all objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
num_layers = 6
angle_increment = 12
fiber_shape_type = "rect"

# Dimensions of the overall structure
structure_height = 2
plate_size = 2
layer_thickness = structure_height / num_layers
fiber_spacing = 0.01

# Function to create a fiber
def create_fiber(shape_type, diameter, position):
    if shape_type == "rect":
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=position, rotation=(0, math.radians(90), 0))
        fiber_cube = bpy.context.object
        fiber_cube.dimensions = (layer_thickness, diameter, plate_size)
        return fiber_cube

# Function to build the helical structure
def build_helical_structure():
    for layer_index in range(num_layers):
        z_position = layer_index * layer_thickness
        rotation_angle = layer_index * angle_increment

        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
        empty_object = bpy.context.object

        fiber_diameter = layer_thickness
        fiber_distance = fiber_diameter + fiber_spacing
        fiber_count = max(1, int(plate_size / fiber_distance))

        total_fiber_space = fiber_count * fiber_distance
        start_y = -plate_size / 2 + fiber_distance / 2 + (plate_size - total_fiber_space) / 2

        for i in range(fiber_count):
            fiber_y_center = start_y + i * fiber_distance
            fiber_instance = create_fiber(fiber_shape_type, fiber_diameter, (0, fiber_y_center, z_position))
            fiber_instance.parent = empty_object
            fiber_instance.matrix_parent_inverse = empty_object.matrix_world.inverted()

        empty_object.rotation_euler[2] = math.radians(rotation_angle)

# Execute the building of the helical structure
build_helical_structure()
