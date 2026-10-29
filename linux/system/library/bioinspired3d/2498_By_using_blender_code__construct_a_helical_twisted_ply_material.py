# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_code__construct_a_helical_twisted_ply_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender code, construct a helical twisted ply material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical formation
ply_count = 7  # Number of plies
rotation_angle = 15  # Rotation in degrees per ply

class HelicalPlate:
    def __init__(self, index):
        self.index = index
        self.height = 2  # Total height
        self.size = 2  # Side length of the plate
        self.thickness = self.height / ply_count  # Thickness of each ply
        self.create_plate()

    def create_plate(self):
        z_position = self.index * self.thickness
        bpy.ops.mesh.primitive_cube_add(size=self.size, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = self.thickness / 2
        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(self.index * rotation_angle), orient_axis='Z')

for i in range(0, ply_count):
    HelicalPlate(i)
