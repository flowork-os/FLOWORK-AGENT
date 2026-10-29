# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_code__generate_a_model_of_a_helical_bioinspired_material_with_eac" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender code, generate a model of a helical bioinspired material with each layer formed by rectangular fibers. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 7
rotation_angle = 10
fiber_form = "rect"

complete_height = 2
plate_dimension = 2
thickness_per_layer = complete_height / layer_count
fiber_spacing = 0.01

class Fiber:
    @staticmethod
    def add(shape, diameter, location):
        if shape == "rect":
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=(0, math.radians(90), 0))
            cube = bpy.context.object
            cube.dimensions = (thickness_per_layer, diameter, plate_dimension)
            return cube

class HelicalStructure:
    def __init__(self, layer_count, rotation_angle):
        self.layer_count = layer_count
        self.rotation_angle = rotation_angle

    def create_layer(self, index):
        height_position = index * thickness_per_layer
        rotation_for_layer = index * self.rotation_angle

        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_position))
        empty_layer = bpy.context.object

        fiber_diameter = thickness_per_layer
        spacing_between_fibers = fiber_diameter + fiber_spacing
        number_of_fibers = max(1, int(plate_dimension / spacing_between_fibers))

        total_length = number_of_fibers * spacing_between_fibers
        start_y = -plate_dimension / 2 + spacing_between_fibers / 2 + (plate_dimension - total_length) / 2

        for i in range(number_of_fibers):
            fiber_y_position = start_y + i * spacing_between_fibers
            fiber_instance = Fiber.add(fiber_form, fiber_diameter, (0, fiber_y_position, height_position))
            fiber_instance.parent = empty_layer
            fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

        empty_layer.rotation_euler[2] = math.radians(rotation_for_layer)

    def build(self):
        for i in range(self.layer_count):
            self.create_layer(i)

helical_model = HelicalStructure(layer_count, rotation_angle)
helical_model.build()
