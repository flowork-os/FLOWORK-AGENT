# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_constructs_a_helical_twisted_ply_structure_with_rotational_n" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that constructs a helical twisted ply structure with rotational noise.

import bpy
import math
import random

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure configuration
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

# Instantiate and build the helical structure
helix = HelixBuilder(ply_count, angle_per_ply, apply_noise)
helix.build()
