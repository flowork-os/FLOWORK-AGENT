# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_helical_twisted_ply_bioinspired_material_with_rotational_noise_using_bl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a helical twisted ply bioinspired material with rotational noise using blender code think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for helical structure
ply_count = 12  # Total number of plies
rotation_angle = 5  # Rotation angle for each ply

# Noise settings
is_noise_enabled = True  # Enable noise?
noise_limit = 7  # Max noise in degrees

class HelicalStructure:
    def __init__(self, layers, rotation, noise_enabled, noise_limit):
        self.layers = layers
        self.rotation = rotation
        self.noise_enabled = noise_enabled
        self.noise_limit = noise_limit

    def create_layer(self, index):
        height = 2
        size = 2
        thickness = height / self.layers
        z_position = index * thickness

        # Create a cube at the specified position
        bpy.ops.mesh.primitive_cube_add(
            size=size,
            location=(0, 0, z_position)
        )

        cube = bpy.context.object
        cube.scale[2] = thickness / 2

        # Calculate rotation
        angle = index * self.rotation
        if self.noise_enabled:
            angle += random.uniform(-self.noise_limit, self.noise_limit)

        # Deselect all and select the new cube
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = cube
        cube.select_set(True)

        # Apply rotation
        bpy.ops.transform.rotate(
            value=math.radians(angle),
            orient_axis='Z'
        )

    def build(self):
        for i in range(self.layers):
            self.create_layer(i)

# Create and build the helical structure
helical_model = HelicalStructure(ply_count, rotation_angle, is_noise_enabled, noise_limit)
helical_model.build()
