# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_a_helical_twisted_ply_structure_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of a helical twisted ply structure using blender script

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helix parameters
ply_count = 8  # Number of plies
rotation_angle = 10  # Rotation angle for each ply

# Class to create the helical structure
class HelicalStructure:
    def __init__(self, total_plies, angle):
        self.total_plies = total_plies
        self.angle = angle
        self.height = 2
        self.size = 2
        self.thickness = self.height / self.total_plies

    def create_ply(self, index):
        z_position = index * self.thickness
        bpy.ops.mesh.primitive_cube_add(size=self.size, location=(0, 0, z_position))
        ply = bpy.context.object
        ply.scale[2] = self.thickness / 2
        bpy.context.view_layer.objects.active = ply
        ply.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(index * self.angle), orient_axis='Z')

    def build(self):
        for i in range(self.total_plies):
            self.create_ply(i)

# Instantiate and build the helical structure
helix = HelicalStructure(ply_count, rotation_angle)
helix.build()
