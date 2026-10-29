# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_code_in_Blender__create_a_model_of_a_helical_Bouligand_structure_with_r" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using code in Blender, create a model of a helical Bouligand structure with randomness in rotation think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

ply_count = 8
rotation_angle = 15
apply_noise = True
noise_amount = 4

class HelicalLayer:
    def __init__(self, index):
        self.index = index
        self.layer_height = 2 / ply_count
        self.position_z = index * self.layer_height

    def create(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, self.position_z))
        layer = bpy.context.object
        layer.scale[2] = self.layer_height / 2
        self.apply_rotation(layer)

    def apply_rotation(self, layer):
        base_rotation = self.index * rotation_angle
        if apply_noise:
            base_rotation += random.uniform(-noise_amount, noise_amount)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(base_rotation), orient_axis='Z')

for i in range(ply_count):
    HelicalLayer(i).create()
