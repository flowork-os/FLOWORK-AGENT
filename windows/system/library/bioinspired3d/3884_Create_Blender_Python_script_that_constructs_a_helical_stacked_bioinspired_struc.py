# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_Blender_Python_script_that_constructs_a_helical_stacked_bioinspired_struc" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create Blender Python script that constructs a helical stacked bioinspired structure with noise. think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

plies = 7
rotation_angle = 15
apply_noise = False
noise_amount = 4

class HelicalStructure:
    def __init__(self, plies, rotation_angle, noise_enabled, noise_strength):
        self.plies = plies
        self.rotation_angle = rotation_angle
        self.noise_enabled = noise_enabled
        self.noise_strength = noise_strength

    def create_layer(self, index):
        height = 2
        width = 2
        layer_height = height / self.plies
        z_position = index * layer_height

        bpy.ops.mesh.primitive_cube_add(size=width, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = layer_height / 2

        rotation = index * self.rotation_angle
        if self.noise_enabled:
            rotation += random.uniform(-self.noise_strength, self.noise_strength)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)

        bpy.ops.transform.rotate(value=math.radians(rotation), orient_axis='Z')

    def build(self):
        for i in range(self.plies):
            self.create_layer(i)

helix = HelicalStructure(plies, rotation_angle, apply_noise, noise_amount)
helix.build()
