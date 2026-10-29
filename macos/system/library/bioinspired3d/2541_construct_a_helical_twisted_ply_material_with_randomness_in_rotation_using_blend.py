# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_helical_twisted_ply_material_with_randomness_in_rotation_using_blend" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a helical twisted ply material with randomness in rotation using blender python code

import bpy
import math
import random

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helix parameters
ply_count = 7  # Number of plies
rotation_angle = 10  # Rotation angle in degrees
apply_noise = True  # Whether to add noise
noise_amount = 4  # Noise strength in degrees

class HelicalStructure:
    def __init__(self, layers, angle, noise, noise_strength):
        self.layers = layers
        self.angle = angle
        self.noise = noise
        self.noise_strength = noise_strength

    def create_layer(self, index):
        height = 2
        size = 2
        thickness = height / self.layers
        z_position = index * thickness

        # Add a cube for the layer
        bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = thickness / 2

        # Calculate the rotation angle
        rotation = index * self.angle
        if self.noise:
            rotation += random.uniform(-self.noise_strength, self.noise_strength)

        # Rotate the layer
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(rotation), orient_axis='Z')

    def build(self):
        for i in range(self.layers):
            self.create_layer(i)

# Instantiate and build the helical structure
helical_structure = HelicalStructure(ply_count, rotation_angle, apply_noise, noise_amount)
helical_structure.build()
