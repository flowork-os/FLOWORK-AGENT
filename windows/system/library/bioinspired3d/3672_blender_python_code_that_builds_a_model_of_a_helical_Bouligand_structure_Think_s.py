# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_builds_a_model_of_a_helical_Bouligand_structure_Think_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that builds a model of a helical Bouligand structure Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 8
rotation_angle = 10

class HelicalStructure:
    def __init__(self, layers, angle):
        self.layers = layers
        self.angle = angle
        self.height = 2
        self.size = 2

    def create_layer(self, index):
        thickness = self.height / self.layers
        z_position = index * thickness
        bpy.ops.mesh.primitive_cube_add(size=self.size, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = thickness / 2
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(index * self.angle), orient_axis='Z')

    def build(self):
        for i in range(self.layers):
            self.create_layer(i)

helical = HelicalStructure(num_layers, rotation_angle)
helical.build()
