# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_code__create_a_model_of_a_helical_twisted_ply_structure__Think_ste" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender code, create a model of a helical twisted ply structure. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical structure parameters
ply_count = 12  # Total number of plies
rotation_step = 18  # Degrees of rotation for each ply

class HelicalStructure:
    def __init__(self, layers, rotation):
        self.layers = layers
        self.rotation = rotation
        self.total_height = 2
        self.plate_size = 2

    def create_ply(self, index):
        thickness = self.total_height / self.layers
        z_position = index * thickness

        # Add a plate at the specified height
        bpy.ops.mesh.primitive_cube_add(size=self.plate_size, location=(0, 0, z_position))
        current_plate = bpy.context.object
        current_plate.scale[2] = thickness / 2

        # Rotate the plate
        bpy.ops.transform.rotate(value=math.radians(index * self.rotation), orient_axis='Z')

    def build(self):
        for i in range(self.layers):
            self.create_ply(i)

# Create and build the helical structure
helical_model = HelicalStructure(ply_count, rotation_step)
helical_model.build()
