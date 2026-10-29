# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_helical_twisted_ply_bioinspired_structure_using_code_in_Blender_Think" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a helical twisted ply bioinspired structure using code in Blender Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_number = 15  # Total layers
rotation_degree = 6  # Degrees of rotation per layer

class HelicalStructure:
    def __init__(self, layers, rotation):
        self.layers = layers
        self.rotation = rotation

    def create_layer(self, index):
        total_height = 2
        plate_dimension = 2
        thickness = total_height / self.layers
        z_coord = index * thickness

        bpy.ops.mesh.primitive_cube_add(
            size=plate_dimension,
            location=(0, 0, z_coord)
        )
        layer = bpy.context.object
        layer.scale[2] = thickness / 2

        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(
            value=math.radians(index * self.rotation),
            orient_axis='Z'
        )

    def build(self):
        for i in range(self.layers):
            self.create_layer(i)

helical_model = HelicalStructure(layer_number, rotation_degree)
helical_model.build()
