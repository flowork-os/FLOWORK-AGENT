# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_Blender_Python_script_that_constructs_a_helical_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create Blender Python script that constructs a helical material.

import bpy
import math

# Clear existing objects in the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
ply_count = 8  # Number of plies in the helical structure
rotation_angle = 10  # Rotation angle for each ply

class HelixBuilder:
    def __init__(self, total_plys, angle):
        self.total_plys = total_plys
        self.angle = angle
        self.final_height = 2
        self.plate_size = 2
        self.thickness = self.final_height / self.total_plys

    def create_helix(self):
        for i in range(self.total_plys):
            self.create_single_ply(i)

    def create_single_ply(self, index):
        z_position = index * self.thickness
        bpy.ops.mesh.primitive_cube_add(size=self.plate_size, location=(0, 0, z_position))
        ply = bpy.context.object
        ply.scale[2] = self.thickness / 2
        bpy.context.view_layer.objects.active = ply
        ply.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(index * self.angle), orient_axis='Z')

# Instantiate and create the helical structure
helix = HelixBuilder(ply_count, rotation_angle)
helix.create_helix()
