# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_a_helical_twisted_ply_structure_in_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of a helical twisted ply structure in Blender Python script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
number_of_layers = 8  # Number of layers in the helical structure
rotation_angle = 10  # Rotation angle for each layer

class HelicalPlate:
    def __init__(self, index):
        self.index = index
        self.height = 2
        self.size = 2
        self.thickness = self.height / number_of_layers
        self.z_position = self.index * self.thickness
        self.create_plate()

    def create_plate(self):
        bpy.ops.mesh.primitive_cube_add(size=self.size, location=(0, 0, self.z_position))
        plate = bpy.context.object
        plate.scale[2] = self.thickness / 2
        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(self.index * rotation_angle), orient_axis='Z')

# Generate helical structure
for i in range(number_of_layers):
    HelicalPlate(i)
