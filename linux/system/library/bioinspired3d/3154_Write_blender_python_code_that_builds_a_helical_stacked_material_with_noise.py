# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_python_code_that_builds_a_helical_stacked_material_with_noise" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender python code that builds a helical stacked material with noise.

import bpy
import math
import random

# Clear existing objects in the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helix parameters
ply_count = 8  # Number of layers in the helical structure
rotation_step = 10  # Angle increment per layer
noise_enabled = True  # Enable noise in rotation
noise_amount = 7  # Maximum rotation noise

class HelicalStructure:
    def __init__(self, layers, rotation, noise):
        self.layers = layers
        self.rotation = rotation
        self.noise = noise

    def create_layer(self, index):
        z_position = index * (2 / self.layers)
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = (2 / self.layers) / 2

        base_rotation = index * self.rotation
        if noise_enabled:
            base_rotation += random.uniform(-self.noise, self.noise)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(base_rotation), orient_axis='Z')
        return layer

helical_model = HelicalStructure(ply_count, rotation_step, noise_amount)
for i in range(helical_model.layers):
    helical_model.create_layer(i)
