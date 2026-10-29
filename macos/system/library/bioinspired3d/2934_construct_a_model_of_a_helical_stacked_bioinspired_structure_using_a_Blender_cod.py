# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_a_helical_stacked_bioinspired_structure_using_a_Blender_cod" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of a helical stacked bioinspired structure using a Blender code

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
num_layers = 12
rotation_step = 5

class HelicalPlate:
    def __init__(self, index):
        self.index = index
        self.height = 2
        self.size = 2
        self.thickness = self.height / num_layers

    def create(self):
        z_position = self.index * self.thickness
        bpy.ops.mesh.primitive_cube_add(size=self.size, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = self.thickness / 2
        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(self.index * rotation_step), orient_axis='Z')

for i in range(num_layers):
    HelicalPlate(i).create()
