# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_Blender_Python_script__create_a_helical_twisted_ply_bioinspired_structu" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using Blender Python script, create a helical twisted ply bioinspired structure made of cylindrical fibers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for helical fiber arrangement
num_layers = 7  # Number of layers
layer_rotation = 10  # Rotation in degrees for each layer
fiber_shape_type = 'cylinder'  # Shape of the fibers

# Dimensions of the entire structure
height_of_structure = 2.0  # Total height
plate_dimensions = 2.0  # Width and length of each plate
thickness_per_layer = height_of_structure / num_layers  # Thickness of each layer

class FiberStructure:
    def __init__(self, shape, thickness, plate_dim):
        self.shape = shape
        self.thickness = thickness
        self.plate_dim = plate_dim

    def add_fiber(self, x, y, z):
        bpy.ops.mesh.primitive_cylinder_add(
            radius=self.thickness / 2,
            depth=self.plate_dim,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )

    def create_layer(self, index):
        z_position = index * self.thickness
        rotation_angle = index * layer_rotation

        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
        layer_empty = bpy.context.object

        fiber_count = max(1, int(self.plate_dim / self.thickness))
        start_y = -self.plate_dim / 2 + (self.thickness / 2) + (self.plate_dim - fiber_count * self.thickness) / 2

        for i in range(fiber_count):
            fiber_y = start_y + i * self.thickness
            self.add_fiber(0, fiber_y, z_position)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer_empty
        layer_empty.select_set(True)

        bpy.ops.transform.rotate(
            value=math.radians(rotation_angle),
            orient_axis='Z'
        )

# Instantiate the structure
fiber_structure = FiberStructure(fiber_shape_type, thickness_per_layer, plate_dimensions)

# Build the helical structure
for i in range(num_layers):
    fiber_structure.create_layer(i)
