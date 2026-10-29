# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_for_constructing_a_helical_stacked_bioinspired_structure_with_noi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code for constructing a helical stacked bioinspired structure with noise. Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_count = 12  # Total plies
angle_step = 5  # Rotation in degrees for each layer

# Noise configuration
add_noise = True  # Noise toggle
max_variation = 4  # Noise strength

class HelicalStructure:
    def __init__(self, layer_count, angle_step, add_noise, max_variation):
        self.layer_count = layer_count
        self.angle_step = angle_step
        self.add_noise = add_noise
        self.max_variation = max_variation

    def create_layer(self, index):
        height = 2
        size = 2
        thickness = height / self.layer_count
        z_position = index * thickness

        # Create cube
        bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = thickness / 2

        # Calculate rotation
        rotation = index * self.angle_step
        if self.add_noise:
            rotation += random.uniform(-self.max_variation, self.max_variation)

        # Rotate the layer
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)

        bpy.ops.transform.rotate(value=math.radians(rotation), orient_axis='Z')

    def build(self):
        for i in range(self.layer_count):
            self.create_layer(i)

# Instantiate and build the helical structure
helical = HelicalStructure(layer_count, angle_step, add_noise, max_variation)
helical.build()
