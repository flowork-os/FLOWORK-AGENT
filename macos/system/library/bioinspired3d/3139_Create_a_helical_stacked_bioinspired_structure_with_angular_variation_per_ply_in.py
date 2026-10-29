# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_helical_stacked_bioinspired_structure_with_angular_variation_per_ply_in" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a helical stacked bioinspired structure with angular variation per ply in a Blender code

import bpy
import math
import random

# Clear existing objects in the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helix parameters
ply_count = 8
rotation_angle = 15
apply_noise = True
noise_amount = 4

class HelicalLayer:
    def __init__(self, index):
        self.index = index
        self.layer_height = 2 / ply_count
        self.position_z = index * self.layer_height

    def create(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, self.position_z))
        layer = bpy.context.object
        layer.scale[2] = self.layer_height / 2
        self.apply_rotation(layer)

    def apply_rotation(self, layer):
        base_rotation = self.index * rotation_angle
        if apply_noise:
            base_rotation += random.uniform(-noise_amount, noise_amount)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(base_rotation), orient_axis='Z')

# Generate the helical structure
for i in range(ply_count):
    HelicalLayer(i).create()
