# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_tubular_structure_with_noise_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a tubular structure with noise in Blender code

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule configuration
total_tubules = 25
deviation = 0.1

class TubuleCreator:
    def __init__(self, count, noise):
        self.count = count
        self.noise = noise
        self.cube = None

    def setup_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.cube = bpy.context.object

    def generate_positions(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2
        return [(offset + (i % grid_size) * spacing,
                 offset + (i // grid_size) * spacing)
                for i in range(self.count)]

    def apply_noise(self, positions):
        return [(x + random.uniform(-self.noise, self.noise),
                 y + random.uniform(-self.noise, self.noise))
                for x, y in positions]

    def create_tubules(self):
        self.setup_cube()
        positions = self.generate_positions()
        noisy_positions = self.apply_noise(positions)

        for x, y in noisy_positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            modifier = self.cube.modifiers.new(name=f"Remove_{x}_{y}", type='BOOLEAN')
            modifier.operation = 'DIFFERENCE'
            modifier.object = tubule
            bpy.context.view_layer.objects.active = self.cube
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Create the structure
creator = TubuleCreator(total_tubules, deviation)
creator.create_tubules()
