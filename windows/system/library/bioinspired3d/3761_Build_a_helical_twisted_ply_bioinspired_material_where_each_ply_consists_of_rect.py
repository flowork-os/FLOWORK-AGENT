# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_helical_twisted_ply_bioinspired_material_where_each_ply_consists_of_rect" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a helical twisted ply bioinspired material where each ply consists of rectangular fibers in python blender code Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 9  # Total layers in the structure
rotation_angle = 20  # Degrees of rotation for each layer
fiber_shape = 'rect'  # Shape of fibers used

structure_height = 2  # Overall height of the structure
plate_size = 2  # Width and length of each plate
ply_thickness = structure_height / layer_count  # Thickness of each ply
fiber_gap = 0.01  # Gap between fibers

class Fiber:
    def __init__(self, shape, diameter, position):
        self.shape = shape
        self.diameter = diameter
        self.position = position

    def add_to_scene(self, thickness):
        if self.shape == 'rect':
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=self.position, rotation=(0, math.radians(90), 0))
            fiber = bpy.context.object
            fiber.dimensions = (thickness, self.diameter, plate_size)
            return fiber

def create_layer(layer_index):
    z_position = layer_index * ply_thickness
    rotation = layer_index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = ply_thickness
    fiber_spacing = fiber_diameter + fiber_gap
    fiber_count = max(1, int(plate_size / fiber_spacing))

    total_fiber_space = fiber_count * fiber_spacing
    start_y = -plate_size / 2 + fiber_spacing / 2 + (plate_size - total_fiber_space) / 2

    for i in range(fiber_count):
        current_y = start_y + i * fiber_spacing
        fiber = Fiber(shape=fiber_shape, diameter=fiber_diameter, position=(0, current_y, z_position))
        fiber_instance = fiber.add_to_scene(thickness=ply_thickness)
        fiber_instance.parent = layer_empty
        fiber_instance.matrix_parent_inverse = layer_empty.matrix_world.inverted()

    layer_empty.rotation_euler[2] = math.radians(rotation)
    return layer_empty

for i in range(layer_count):
    create_layer(i)
