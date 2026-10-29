# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_helical_stacked_structure_with_angular_variation_per_ply_u" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a helical stacked structure with angular variation per ply using blender script

import bpy
import math
import random

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
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

        # Add a cube at the specified location
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = layer_thickness / 2

        # Calculate rotation angle
        angle = index * self.rotation
        if self.noise:
            angle += random.uniform(-self.noise_strength, self.noise_strength)

        # Rotate the layer
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(angle), orient_axis='Z')

    def build(self):
        for i in range(self.layers):
            self.create_layer(i)

# Instantiate and build the helix
helix = HelixBuilder(num_layers, rotation_step, noise_enabled, noise_amount)
helix.build()
