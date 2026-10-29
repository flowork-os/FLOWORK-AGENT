# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_generates_a_model_of_a_helical_bioinspired_structure_with_rota" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that generates a model of a helical bioinspired structure with rotational noise.

import bpy
import math
import random

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure specifications
layer_count = 15  # Total number of layers
angle_increment = 5  # Degrees of rotation per layer
add_noise = True  # Add noise to rotation
noise_degree = 9  # Max noise in degrees

class HelicalStructure:
    def __init__(self, layers, angle, noise, noise_strength):
        self.layers = layers
        self.angle = angle
        self.noise = noise
        self.noise_strength = noise_strength

    def build_layer(self, index):
        height = 2
        cube_size = 2
        layer_height = height / self.layers
        z_position = index * layer_height

        # Create cube at specified location
        bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = layer_height / 2

        # Compute rotation angle
        rotation_value = index * self.angle
        if self.noise:
            rotation_value += random.uniform(-self.noise_strength, self.noise_strength)

        # Select and rotate the layer
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')

    def create_structure(self):
        for i in range(self.layers):
            self.build_layer(i)

# Instantiate and create the helical structure
helical_structure = HelicalStructure(layer_count, angle_increment, add_noise, noise_degree)
helical_structure.create_structure()
