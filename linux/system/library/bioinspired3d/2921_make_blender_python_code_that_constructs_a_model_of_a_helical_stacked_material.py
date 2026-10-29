# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_blender_python_code_that_constructs_a_model_of_a_helical_stacked_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make blender python code that constructs a model of a helical stacked material.

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
