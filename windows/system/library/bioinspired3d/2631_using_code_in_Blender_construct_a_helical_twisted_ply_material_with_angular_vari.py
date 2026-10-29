# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_code_in_Blender_construct_a_helical_twisted_ply_material_with_angular_vari" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using code in Blender construct a helical twisted ply material with angular variation per ply. Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure settings
plies = 7
angle_per_ply = 10
add_noise = True
noise_amount = 4

class HelicalPlate:
    def __init__(self, index):
        self.index = index
        self.height = 2
        self.size = 2
        self.thickness = self.height / plies
        self.z_position = self.index * self.thickness

    def create(self):
        bpy.ops.mesh.primitive_cube_add(size=self.size, location=(0, 0, self.z_position))
        plate = bpy.context.object
        plate.scale[2] = self.thickness / 2
        return plate

    def rotate(self, plate):
        base_rotation = self.index * angle_per_ply
        if add_noise:
            base_rotation += random.uniform(-noise_amount, noise_amount)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(base_rotation), orient_axis='Z')

# Generate the helical structure
for i in range(plies):
    plate = HelicalPlate(i)
    created_plate = plate.create()
    plate.rotate(created_plate)
