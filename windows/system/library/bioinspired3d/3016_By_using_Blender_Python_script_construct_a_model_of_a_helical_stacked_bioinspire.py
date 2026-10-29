# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_Python_script_construct_a_model_of_a_helical_stacked_bioinspire" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender Python script construct a model of a helical stacked bioinspired structure with flat rectangular struts in each layer.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber design
layers = 9  # Number of layers in the helical structure
rotation_step = 5  # Rotation in degrees per layer
fiber_form = 'rect'

# Dimensions of the structure
height_of_design = 2.0  # Total height of the structure
plate_dim = 2.0  # Size of each square plate
layer_thickness = height_of_design / layers  # Thickness of each layer
fiber_separation = 0.01  # Small gap between fibers

class HelicalFiber:
    def __init__(self, form, thickness, dimension, rotation):
        self.form = form
        self.thickness = thickness
        self.dimension = dimension
        self.rotation = rotation

    def create_fiber(self, x, y, z):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z), rotation=(0, math.radians(90), 0))
        fiber_obj = bpy.context.object
        fiber_obj.dimensions = (self.thickness, self.thickness, self.dimension)
        return fiber_obj

    def build_layer(self, index):
        z_position = index * self.thickness
        layer_rotation = index * self.rotation

        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
        empty_layer = bpy.context.object

        fiber_diameter = self.thickness
        spacing = fiber_diameter + fiber_separation
        fiber_count = max(1, int(self.dimension / spacing))

        total_fiber_length = fiber_count * spacing
        start_y = -self.dimension / 2 + spacing / 2 + (self.dimension - total_fiber_length) / 2

        for i in range(fiber_count):
            fiber_center_y = start_y + i * spacing
            fiber_instance = self.create_fiber(0, fiber_center_y, z_position)
            fiber_instance.parent = empty_layer
            fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

        empty_layer.rotation_euler[2] = math.radians(layer_rotation)
        return empty_layer

# Instantiate and build the helical structure
helical_fiber = HelicalFiber(fiber_form, layer_thickness, plate_dim, rotation_step)
for i in range(layers):
    helical_fiber.build_layer(i)
