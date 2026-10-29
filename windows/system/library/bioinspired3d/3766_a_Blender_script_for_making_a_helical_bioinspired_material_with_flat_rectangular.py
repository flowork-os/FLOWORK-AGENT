# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_for_making_a_helical_bioinspired_material_with_flat_rectangular" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script for making a helical bioinspired material with flat rectangular struts in each layer. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_num = 8
rotation_step = 5
fiber_form_type = "rect"

height_total = 2
plate_dim = 2
thickness_per_layer = height_total / layer_num
fiber_spacing_distance = 0.01

class FiberLayer:
    def __init__(self, index):
        self.index = index
        self.height = self.index * thickness_per_layer
        self.rotation = self.index * rotation_step

    def create_empty(self):
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, self.height))
        return bpy.context.object

    def generate_fibers(self, empty_object):
        fiber_diameter = thickness_per_layer
        fiber_distance = fiber_diameter + fiber_spacing_distance
        fiber_count = max(1, int(plate_dim / fiber_distance))

        total_fiber_space = fiber_count * fiber_distance
        start_y = -plate_dim / 2 + fiber_distance / 2 + (plate_dim - total_fiber_space) / 2

        for i in range(fiber_count):
            fiber_y_center = start_y + i * fiber_distance
            fiber_instance = self.add_fiber(fiber_form_type, fiber_diameter, 0, fiber_y_center, self.height)
            fiber_instance.parent = empty_object
            fiber_instance.matrix_parent_inverse = empty_object.matrix_world.inverted()

    @staticmethod
    def add_fiber(shape_type, diameter, x, y, z):
        if shape_type == "rect":
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z), rotation=(0, math.radians(90), 0))
            fiber = bpy.context.object
            fiber.dimensions = (thickness_per_layer, diameter, plate_dim)
            return fiber

for i in range(layer_num):
    layer = FiberLayer(i)
    empty_object = layer.create_empty()
    layer.generate_fibers(empty_object)
    empty_object.rotation_euler[2] = math.radians(layer.rotation)
