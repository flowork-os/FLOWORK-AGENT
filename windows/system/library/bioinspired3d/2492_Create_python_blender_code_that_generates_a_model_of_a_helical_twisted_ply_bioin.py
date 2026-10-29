# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_python_blender_code_that_generates_a_model_of_a_helical_twisted_ply_bioin" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create python blender code that generates a model of a helical twisted ply bioinspired material

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
num_layers = 7
rotation_angle = 20

class HelicalStructure:
    def __init__(self, num_layers, rotation_angle):
        self.num_layers = num_layers
        self.rotation_angle = rotation_angle
        self.total_height = 2
        self.layer_size = 2

    def create_layer(self, index):
        layer_height = self.total_height / self.num_layers
        z_position = index * layer_height

        bpy.ops.mesh.primitive_cube_add(size=self.layer_size, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = layer_height / 2

        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(index * self.rotation_angle), orient_axis='Z')

    def build_structure(self):
        for i in range(self.num_layers):
            self.create_layer(i)

# Instantiate and build the helical structure
helical_structure = HelicalStructure(num_layers, rotation_angle)
helical_structure.build_structure()
