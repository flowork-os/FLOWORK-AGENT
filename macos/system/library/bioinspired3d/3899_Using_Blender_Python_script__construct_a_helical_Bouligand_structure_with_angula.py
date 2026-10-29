# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_Blender_Python_script__construct_a_helical_Bouligand_structure_with_angula" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using Blender Python script, construct a helical Bouligand structure with angular variation per ply Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 7  # Number of layers in the structure
rotation_step = 10  # Rotation angle for each layer
noise_enabled = True  # Enable rotation noise
noise_amount = 4  # Maximum noise in degrees

class HelixBuilder:
    def __init__(self, layers, rotation, noise, noise_strength):
        self.layers = layers
        self.rotation = rotation
        self.noise = noise
        self.noise_strength = noise_strength

    def create_layer(self, index):
        height = 2
        layer_thickness = height / self.layers
        z_position = index * layer_thickness

        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = layer_thickness / 2

        angle = index * self.rotation
        if self.noise:
            angle += random.uniform(-self.noise_strength, self.noise_strength)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)

        bpy.ops.transform.rotate(value=math.radians(angle), orient_axis='Z')

    def build(self):
        for i in range(self.layers):
            self.create_layer(i)

helix = HelixBuilder(num_layers, rotation_step, noise_enabled, noise_amount)
helix.build()
