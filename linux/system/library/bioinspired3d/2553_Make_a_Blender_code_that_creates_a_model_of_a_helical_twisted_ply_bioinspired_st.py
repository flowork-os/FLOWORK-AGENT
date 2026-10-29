# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_Blender_code_that_creates_a_model_of_a_helical_twisted_ply_bioinspired_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a Blender code that creates a model of a helical twisted ply bioinspired structure with angular variation per ply.

import bpy
import math
import random

# Clear existing objects from the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helix parameters
plies_total = 10  # Number of plies in the helical structure
angle_per_ply = 7  # Rotation angle per layer
noise_active = True  # Whether to apply noise
max_noise = 4  # Max noise in degrees

class HelicalStructure:
    def __init__(self, total_plies, rotation_angle, noise, noise_strength):
        self.total_plies = total_plies
        self.rotation_angle = rotation_angle
        self.noise = noise
        self.noise_strength = noise_strength

    def create_layer(self, index):
        height_per_layer = 2 / self.total_plies
        z_position = index * height_per_layer

        # Create the cube layer
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = height_per_layer / 2

        # Calculate rotation with noise
        rotation_value = index * self.rotation_angle
        if self.noise:
            rotation_value += random.uniform(-self.noise_strength, self.noise_strength)

        # Activate layer for rotation
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)

        # Rotate the layer
        bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')

    def build_structure(self):
        for i in range(self.total_plies):
            self.create_layer(i)

# Instantiate and build the helical structure
helical_model = HelicalStructure(plies_total, angle_per_ply, noise_active, max_noise)
helical_model.build_structure()
