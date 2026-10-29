# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_a_helical_structure_in_blender_code_think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of a helical structure in blender code think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 8  # Number of layers in the helical structure
rotation_angle = 10  # Angle for each layer rotation

class HelicalPlate:
    def __init__(self, index):
        self.index = index
        self.height = 2  # Total height of the structure
        self.size = 2  # Size of each plate
        self.thickness = self.height / num_layers  # Thickness calculation

    def create(self):
        z_position = self.index * self.thickness
        bpy.ops.mesh.primitive_cube_add(size=self.size, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = self.thickness / 2
        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(self.index * rotation_angle), orient_axis='Z')

for layer in range(num_layers):
    HelicalPlate(layer).create()
