# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_python_blender_code_generate_a_helical_Bouligand_structure_with_noise" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With python blender code generate a helical Bouligand structure with noise

import bpy
import math
import random

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure settings
num_layers = 7
rotation_angle = 12
randomize_rotation = True
noise_amount = 4

class HelixBuilder:
    def __init__(self, layers, angle, noise):
        self.layers = layers
        self.angle = angle
        self.noise = noise

    def create_layer(self, index):
        height = 2
        size = 2
        thickness = height / self.layers
        z_position = index * thickness

        bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
        current_layer = bpy.context.object
        current_layer.scale[2] = thickness / 2

        rotation = index * self.angle
        if self.noise:
            rotation += random.uniform(-self.noise, self.noise)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = current_layer
        current_layer.select_set(True)

        bpy.ops.transform.rotate(value=math.radians(rotation), orient_axis='Z')

    def build(self):
        for i in range(self.layers):
            self.create_layer(i)

# Instantiate and build the helical structure
helix = HelixBuilder(num_layers, rotation_angle, randomize_rotation)
helix.build()
