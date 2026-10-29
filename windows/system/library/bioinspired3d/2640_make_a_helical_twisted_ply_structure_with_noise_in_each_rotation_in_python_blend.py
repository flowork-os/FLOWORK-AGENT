# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_helical_twisted_ply_structure_with_noise_in_each_rotation_in_python_blend" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a helical twisted ply structure with noise in each rotation in python blender code think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

ply_count = 8
rotation_step = 10
apply_noise = True
noise_amount = 4

class HelixBuilder:
    def __init__(self, layers, rotation, noise):
        self.layers = layers
        self.rotation = rotation
        self.noise = noise

    def create_layer(self, index):
        height = 2
        base_size = 2
        layer_thickness = height / self.layers
        z_position = index * layer_thickness

        bpy.ops.mesh.primitive_cube_add(size=base_size, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = layer_thickness / 2

        base_rotation = index * self.rotation
        if apply_noise:
            base_rotation += random.uniform(-self.noise, self.noise)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(base_rotation), orient_axis='Z')

    def build(self):
        for i in range(self.layers):
            self.create_layer(i)

helix = HelixBuilder(ply_count, rotation_step, noise_amount)
helix.build()
