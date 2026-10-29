# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_helical_twisted_ply_material_in_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a helical twisted ply material in a Blender code

import bpy
import math

# Clear existing objects from the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical structure parameters
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
