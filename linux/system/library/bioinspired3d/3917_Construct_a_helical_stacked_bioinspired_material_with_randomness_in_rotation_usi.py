# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_helical_stacked_bioinspired_material_with_randomness_in_rotation_usi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a helical stacked bioinspired material with randomness in rotation using a Blender script think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

ply_count = 7
rotation_step = 10
add_noise = True
noise_amount = 5

class HelicalStructure:
    def __init__(self, layers, rotation, noise):
        self.layers = layers
        self.rotation = rotation
        self.noise = noise

    def create_layer(self, index):
        height = 2
        size = 2
        thickness = height / self.layers
        z_position = index * thickness

        bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = thickness / 2

        angle = index * self.rotation
        if self.noise:
            angle += random.uniform(-self.noise, self.noise)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)

        bpy.ops.transform.rotate(value=math.radians(angle), orient_axis='Z')

    def build(self):
        for i in range(self.layers):
            self.create_layer(i)

helical = HelicalStructure(ply_count, rotation_step, add_noise)
helical.build()
