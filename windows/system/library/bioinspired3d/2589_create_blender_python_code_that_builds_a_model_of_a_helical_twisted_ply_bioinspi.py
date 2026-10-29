# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_blender_python_code_that_builds_a_model_of_a_helical_twisted_ply_bioinspi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create blender python code that builds a model of a helical twisted ply bioinspired structure Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 7  # Number of layers in the helical structure
rotation_degree = 10  # Rotation angle for each layer

class HelicalStructure:
    def __init__(self, layers, rotation):
        self.layers = layers
        self.rotation = rotation
        self.height = 2
        self.size = 2

    def create_layer(self, index):
        layer_thickness = self.height / self.layers
        z_position = index * layer_thickness

        bpy.ops.mesh.primitive_cube_add(size=self.size, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = layer_thickness / 2

        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(index * self.rotation), orient_axis='Z')

    def build(self):
        for i in range(self.layers):
            self.create_layer(i)

helical = HelicalStructure(num_layers, rotation_degree)
helical.build()
