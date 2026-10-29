# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_code_generate_a_model_of_a_helical_Bouligand_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender code generate a model of a helical Bouligand material.

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helix parameters
num_layers = 7  # Number of layers in the helical structure
rotation_degree = 10  # Rotation angle for each layer

class HelicalStructure:
    def __init__(self, layers, rotation):
        self.layers = layers
        self.rotation = rotation
        self.height = 2
        self.size = 2

    def create_layer(self, index):
        # Create a single layer of the helical structure
        layer_thickness = self.height / self.layers
        z_position = index * layer_thickness

        # Add a cube mesh at the calculated position
        bpy.ops.mesh.primitive_cube_add(size=self.size, location=(0, 0, z_position))
        layer = bpy.context.object
        layer.scale[2] = layer_thickness / 2

        # Rotate the layer around the Z-axis
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(index * self.rotation), orient_axis='Z')

    def build(self):
        for i in range(self.layers):
            self.create_layer(i)

# Instantiate and build the helical structure
helical = HelicalStructure(num_layers, rotation_degree)
helical.build()
