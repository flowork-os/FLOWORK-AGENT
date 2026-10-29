# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_for_creating_a_model_of_a_helical_stacked_bioinspired_material_w" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender for creating a model of a helical stacked bioinspired material with rotational noise. think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

plys = 8  # Number of layers
rotation_step = 10  # Degrees per layer
add_noise = True  # Whether to include noise
noise_amount = 6  # Degree of noise

class HelicalStructure:
    def __init__(self, layers, rotation, noise, noise_strength):
        self.layers = layers
        self.rotation = rotation
        self.noise = noise
        self.noise_strength = noise_strength

    def create_layer(self, idx):
        height = 2
        width = 2
        layer_height = height / self.layers
        z_pos = idx * layer_height

        bpy.ops.mesh.primitive_cube_add(
            size=width,
            location=(0, 0, z_pos)
        )

        current_layer = bpy.context.object
        current_layer.scale[2] = layer_height / 2

        angle = idx * self.rotation
        if self.noise:
            angle += random.uniform(-self.noise_strength, self.noise_strength)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = current_layer
        current_layer.select_set(True)

        bpy.ops.transform.rotate(
            value=math.radians(angle),
            orient_axis='Z'
        )

helical_model = HelicalStructure(plys, rotation_step, add_noise, noise_amount)
for i in range(helical_model.layers):
    helical_model.create_layer(i)
