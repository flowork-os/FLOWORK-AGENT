# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_for_creating_a_model_of_a_helical_Bouligand_bioinspired_structur" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender for creating a model of a helical Bouligand bioinspired structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure configuration
num_layers = 8  # number of layers in the helical structure
rotation_angle = 10  # rotation angle for each layer

class HelixBuilder:
    def __init__(self, layers, angle):
        self.layers = layers
        self.angle = angle
        self.final_height = 2
        self.plate_size = 2

    def create_layer(self, index):
        layer_thickness = self.final_height / self.layers  # thickness calculation
        z_position = index * layer_thickness  # vertical positioning

        bpy.ops.mesh.primitive_cube_add(size=self.plate_size, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = layer_thickness / 2  # scaling to thin plate

        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(index * self.angle), orient_axis='Z')  # rotation

    def build(self):
        for i in range(self.layers):
            self.create_layer(i)

# Instantiate and build the helical structure
helix = HelixBuilder(num_layers, rotation_angle)
helix.build()
