# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_blender_code__generate_a_model_of_a_helical_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a blender code, generate a model of a helical material

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helix
layers_count = 12
angle_increment = 15

class HelixBuilder:
    def __init__(self, layers, angle):
        self.layers = layers
        self.angle = angle
        self.height = 2
        self.plate_size = 2

    def create_layer(self, index):
        thickness = self.height / self.layers
        z_position = index * thickness

        # Create a new cube
        bpy.ops.mesh.primitive_cube_add(size=self.plate_size, location=(0, 0, z_position))
        layer = bpy.context.object

        # Scale to make it thin
        layer.scale[2] = thickness / 2

        # Rotate the layer
        bpy.ops.transform.rotate(value=math.radians(index * self.angle), orient_axis='Z')

    def build_helical_structure(self):
        for i in range(self.layers):
            self.create_layer(i)

# Instantiate and build the structure
helix = HelixBuilder(layers_count, angle_increment)
helix.build_helical_structure()
