# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_helical_twisted_ply_bioinspired_structure_with_noise_using_blender_scri" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a helical twisted ply bioinspired structure with noise using blender script

import bpy
import math
import random

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure configuration
ply_count = 8
rotation_angle = 10
apply_noise = True
noise_amount = 7

class HelicalStructure:
    def __init__(self, layers, rotation, noise):
        self.layers = layers
        self.rotation = rotation
        self.noise = noise

    def create_layer(self, index):
        height = 2
        cube_size = 2
        thickness = height / self.layers
        z_position = index * thickness

        bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = thickness / 2

        base_rotation = index * self.rotation
        if apply_noise:
            base_rotation += random.uniform(-self.noise, self.noise)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)

        bpy.ops.transform.rotate(value=math.radians(base_rotation), orient_axis='Z')
        return layer

helical_model = HelicalStructure(ply_count, rotation_angle, noise_amount)
for i in range(helical_model.layers):
    helical_model.create_layer(i)
