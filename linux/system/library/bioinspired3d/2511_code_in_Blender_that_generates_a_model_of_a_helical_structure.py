# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_that_generates_a_model_of_a_helical_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender that generates a model of a helical structure.

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
plies = 7  # Total number of plies
angle_per_ply = 15  # Angle of rotation in degrees per ply

class HelixCreator:
    def __init__(self, total_plies, rotation_angle):
        self.total_plies = total_plies
        self.rotation_angle = rotation_angle
        self.structure_height = 2
        self.plate_size = 2

    def create_plate(self, index):
        thickness = self.structure_height / self.total_plies
        z_position = index * thickness

        bpy.ops.mesh.primitive_cube_add(
            size=self.plate_size,
            location=(0, 0, z_position)
        )
        plate = bpy.context.object
        plate.scale[2] = thickness / 2

        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(
            value=math.radians(index * self.rotation_angle),
            orient_axis='Z'
        )

    def build_structure(self):
        for i in range(self.total_plies):
            self.create_plate(i)

# Initialize and build the helical structure
helix = HelixCreator(plies, angle_per_ply)
helix.build_structure()
