# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_helical_twisted_ply_material_with_rotational_noise_using_p" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a helical twisted ply material with rotational noise using python blender code

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure settings
ply_count = 7  # Number of plies
rotation_angle = 10  # Degrees of rotation per ply
add_noise = True  # Introduce noise
noise_amount = 4  # Maximum noise in degrees

class HelicalStructure:
    def __init__(self, layers, rotation, noise, noise_strength):
        self.layers = layers
        self.rotation = rotation
        self.noise = noise
        self.noise_strength = noise_strength

    def create_layer(self, index):
        height = 2
        size = 2
        thickness = height / self.layers
        z_position = index * thickness

        # Create the cube
        bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = thickness / 2

        # Calculate rotation
        base_rotation = index * self.rotation
        if self.noise:
            base_rotation += random.uniform(-self.noise_strength, self.noise_strength)

        # Rotate the layer
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(base_rotation), orient_axis='Z')

    def build_structure(self):
        for i in range(self.layers):
            self.create_layer(i)

# Instantiate and build the helical structure
helical = HelicalStructure(ply_count, rotation_angle, add_noise, noise_amount)
helical.build_structure()
