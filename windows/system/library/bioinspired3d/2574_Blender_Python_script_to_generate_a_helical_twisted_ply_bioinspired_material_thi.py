# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_to_generate_a_helical_twisted_ply_bioinspired_material_thi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script to generate a helical twisted ply bioinspired material think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

ply_count = 7
rotation_step = 20

class HelicalStructure:
    def __init__(self, total_layers, rotation):
        self.total_layers = total_layers
        self.rotation = rotation
        self.height = 2
        self.size = 2

    def create_layer(self, index):
        layer_thickness = self.height / self.total_layers
        z_position = index * layer_thickness

        bpy.ops.mesh.primitive_cube_add(size=self.size, location=(0, 0, z_position))
        current_layer = bpy.context.object
        current_layer.scale[2] = layer_thickness / 2

        bpy.context.view_layer.objects.active = current_layer
        current_layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(index * self.rotation), orient_axis='Z')

    def build(self):
        for i in range(self.total_layers):
            self.create_layer(i)

helical_model = HelicalStructure(ply_count, rotation_step)
helical_model.build()
