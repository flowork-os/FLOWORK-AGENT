# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_for_building_a_tubular_porous_material_with_noisy_tubule_placement" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code for building a tubular porous material with noisy tubule placement Think step by step.

import bpy
import math
import random

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define structure parameters
count = 22  # Total number of tubules
variance = 0.06  # Noise deviation

class TubularStructure:
    def __init__(self, count, variance):
        self.count = count
        self.variance = variance
        self.cube = None

    def create_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.cube = bpy.context.object

    def generate_positions(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2
        return [(offset + (i % grid_size) * spacing, 
                 offset + (i // grid_size) * spacing) for i in range(self.count)]

    def apply_noise(self, positions):
        return [(x + random.uniform(-self.variance, self.variance), 
                 y + random.uniform(-self.variance, self.variance)) for x, y in positions]

    def subtract_tubules(self):
        positions = self.generate_positions()
        noisy_positions = self.apply_noise(positions)
        for x, y in noisy_positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            modifier = self.cube.modifiers.new(name="Subtraction_{:.2f}_{:.2f}".format(x, y), type='BOOLEAN')
            modifier.operation = 'DIFFERENCE'
            modifier.object = tubule
            bpy.context.view_layer.objects.active = self.cube
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Create and generate the tubular structure
structure = TubularStructure(count, variance)
structure.create_cube()
structure.subtract_tubules()
