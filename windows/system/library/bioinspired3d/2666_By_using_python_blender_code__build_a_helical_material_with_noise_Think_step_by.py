# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_python_blender_code__build_a_helical_material_with_noise_Think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using python blender code, build a helical material with noise Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

ply_count = 7
angle_per_ply = 15
apply_noise = True
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
        layer = bpy.context.object
        layer.scale[2] = thickness / 2

        rotation_value = index * self.angle
        if self.noise:
            rotation_value += random.uniform(-noise_amount, noise_amount)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)

        bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')

    def build(self):
        for i in range(self.layers):
            self.create_layer(i)

helix = HelixBuilder(ply_count, angle_per_ply, apply_noise)
helix.build()
