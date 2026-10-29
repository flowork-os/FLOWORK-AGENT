# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_creates_a_model_of_a_helical_stacked_bioinspired_structure_w" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that creates a model of a helical stacked bioinspired structure with flat rectangular struts in each layer. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure parameters
ply_count = 7
rotation_step = 10
fiber_shape_type = 'rect'

# Structure dimensions
height_of_structure = 2
plate_dimension = 2
thickness_of_ply = height_of_structure / ply_count
fiber_spacing = 0.01

class Fiber:
    @staticmethod
    def create_fiber(shape, diameter, position, thickness):
        if shape == 'rect':
            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                location=position,
                rotation=(0, math.radians(90), 0)
            )
            cube = bpy.context.object
            cube.dimensions = (thickness, diameter, plate_dimension)
            return cube

def build_layer(layer_index):
    z_position = layer_index * thickness_of_ply
    rotation_angle = layer_index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_diameter = thickness_of_ply
    fiber_count = max(1, int(plate_dimension / (fiber_diameter + fiber_spacing)))

    start_y = -plate_dimension / 2 + (fiber_spacing / 2) + ((plate_dimension - (fiber_count * (fiber_diameter + fiber_spacing))) / 2)

    for i in range(fiber_count):
        fiber_y = start_y + i * (fiber_diameter + fiber_spacing)
        fiber_instance = Fiber.create_fiber(
            shape=fiber_shape_type,
            diameter=fiber_diameter,
            position=(0, fiber_y, z_position),
            thickness=thickness_of_ply
        )
        fiber_instance.parent = empty_layer
        fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

    empty_layer.rotation_euler[2] = math.radians(rotation_angle)
    return empty_layer

# Create the entire helical structure
for i in range(ply_count):
    build_layer(i)
