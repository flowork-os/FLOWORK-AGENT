# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_Blender_script_that_builds_a_helical_twisted_ply_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a Blender script that builds a helical twisted ply structure

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
ply_count = 7  # Number of plies
rotation_angle = 10  # Rotation angle for each ply

class HelicalStructure:
    def __init__(self, ply_count, rotation_angle):
        self.ply_count = ply_count
        self.rotation_angle = rotation_angle
        self.final_height = 2
        self.plate_size = 2

    def create_ply(self, index):
        thickness = self.final_height / self.ply_count
        z_position = index * thickness

        bpy.ops.mesh.primitive_cube_add(size=self.plate_size, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = thickness / 2

        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(index * self.rotation_angle), orient_axis='Z')

    def build(self):
        for i in range(self.ply_count):
            self.create_ply(i)

helical_structure = HelicalStructure(ply_count, rotation_angle)
helical_structure.build()
