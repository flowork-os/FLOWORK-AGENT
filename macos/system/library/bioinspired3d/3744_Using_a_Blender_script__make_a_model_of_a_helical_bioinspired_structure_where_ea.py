# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_Blender_script__make_a_model_of_a_helical_bioinspired_structure_where_ea" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a Blender script, make a model of a helical bioinspired structure where each ply consists of rectangular fibers Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber assembly
num_layers = 7  # Number of layers in the helical design
layer_rotation = 20  # Rotation in degrees for each layer
fiber_style = 'rect'  # Style of the fibers

# Structure dimensions
height_of_structure = 2.0  # Total height of the structure
size_of_plate = 2.0  # Width and length of each plate
thickness_of_layer = height_of_structure / num_layers  # Layer thickness
fiber_distance = 0.01  # Distance between fibers

class FiberStructure:
    def __init__(self, fiber_style, layer_thickness, plate_size, rotation_angle):
        self.fiber_style = fiber_style
        self.layer_thickness = layer_thickness
        self.plate_size = plate_size
        self.rotation_angle = rotation_angle

    def add_fiber(self, x, y, z):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z), rotation=(0, math.radians(90), 0))
        fiber = bpy.context.object
        fiber.dimensions = (self.layer_thickness, self.layer_thickness, self.plate_size)
        return fiber

    def create_layer(self, index):
        z_position = index * self.layer_thickness
        rotation_for_layer = index * self.rotation_angle

        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
        empty_layer = bpy.context.object

        fiber_diameter = self.layer_thickness
        spacing_between_fibers = fiber_diameter + fiber_distance
        count_of_fibers = max(1, int(self.plate_size / spacing_between_fibers))

        total_fiber_length = count_of_fibers * spacing_between_fibers
        start_y = -self.plate_size / 2 + spacing_between_fibers / 2 + (self.plate_size - total_fiber_length) / 2

        for i in range(count_of_fibers):
            fiber_center_y = start_y + i * spacing_between_fibers
            fiber_instance = self.add_fiber(0, fiber_center_y, z_position)
            fiber_instance.parent = empty_layer
            fiber_instance.matrix_parent_inverse = empty_layer.matrix_world.inverted()

        empty_layer.rotation_euler[2] = math.radians(rotation_for_layer)
        return empty_layer

# Instantiate and create the structure
fiber_structure = FiberStructure(fiber_style, thickness_of_layer, size_of_plate, layer_rotation)
for i in range(num_layers):
    fiber_structure.create_layer(i)
