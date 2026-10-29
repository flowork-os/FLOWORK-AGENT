# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_python_blender_code_make_a_model_of_a_helical_material__Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using python blender code make a model of a helical material. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layers_count = 12
angle_increment = 15

class HelixBuilder:
    def __init__(self, layers, angle):
        self.layers = layers
        self.angle = angle
        self.height = 2
        self.plate_size = 2

    def create_layer(self, index):
        thickness = self.height / self.layers
        z_position = index * thickness

        bpy.ops.mesh.primitive_cube_add(size=self.plate_size, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = thickness / 2

        bpy.ops.transform.rotate(value=math.radians(index * self.angle), orient_axis='Z')

    def build_helical_structure(self):
        for i in range(self.layers):
            self.create_layer(i)

helix = HelixBuilder(layers_count, angle_increment)
helix.build_helical_structure()
