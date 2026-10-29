# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_helical_Bouligand_structure_with_noise_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a helical Bouligand structure with noise in code in Blender

import bpy
import math
import random

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helix parameters
ply_count = 7
rotation_step = 10
add_noise = True
noise_amount = 5

class HelicalStructure:
    def __init__(self, layers, rotation, noise):
        self.layers = layers
        self.rotation = rotation
        self.noise = noise

    def create_layer(self, index):
        height = 2
        size = 2
        thickness = height / self.layers
        z_position = index * thickness

        bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = thickness / 2

        angle = index * self.rotation
        if self.noise:
            angle += random.uniform(-self.noise, self.noise)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)

        bpy.ops.transform.rotate(value=math.radians(angle), orient_axis='Z')

    def build(self):
        for i in range(self.layers):
            self.create_layer(i)

# Initialize and build the structure
helical = HelicalStructure(ply_count, rotation_step, add_noise)
helical.build()
