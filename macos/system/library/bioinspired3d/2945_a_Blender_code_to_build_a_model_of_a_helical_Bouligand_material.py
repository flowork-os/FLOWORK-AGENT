# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_to_build_a_model_of_a_helical_Bouligand_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code to build a model of a helical Bouligand material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical structure parameters
num_layers = 7  # number of layers in the structure
rotation_angle = 10  # rotation angle for each layer

class HelicalPlate:
    def __init__(self, index):
        self.index = index
        self.height = 2
        self.size = 2
        self.thickness = self.height / num_layers
        self.z_position = self.index * self.thickness

    def create(self):
        # Add a cube at the specified Z position
        bpy.ops.mesh.primitive_cube_add(size=self.size, location=(0, 0, self.z_position))
        plate = bpy.context.object
        plate.scale[2] = self.thickness / 2
        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(self.index * rotation_angle), orient_axis='Z')

# Generate the helical plates
for i in range(num_layers):
    HelicalPlate(i).create()
