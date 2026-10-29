# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_generating_a_helical_twisted_ply_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for generating a helical twisted ply bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
num_layers = 8  # Total layers in the structure
rotation_angle = 10  # Degrees of rotation for each layer

class HelixBuilder:
    def __init__(self, layers, angle):
        self.layers = layers
        self.angle = angle

    def create_plate(self, index):
        height = 2  # Overall height
        size = 2  # Size of the square plate
        thickness = height / self.layers  # Thickness of each layer

        z_position = index * thickness  # Vertical position

        bpy.ops.mesh.primitive_cube_add(
            size=size,
            location=(0, 0, z_position)
        )

        plate = bpy.context.object
        plate.scale[2] = thickness / 2

        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)

        bpy.ops.transform.rotate(
            value=math.radians(index * self.angle),
            orient_axis='Z'
        )

    def generate(self):
        for i in range(self.layers):
            self.create_plate(i)

# Instantiate the helix builder and generate the structure
helix = HelixBuilder(num_layers, rotation_angle)
helix.generate()
