# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_generating_a_model_of_a_tubular_bioinspired_structure_with_ra" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for generating a model of a tubular bioinspired structure with random placement. Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
num_tubules = 12
noise_amount = 0.05

class TubuleCreator:
    def __init__(self, count, noise):
        self.count = count
        self.noise = noise

    def create_structure(self):
        self._add_cube()
        self._place_tubules()

    def _add_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.cube = bpy.context.object

    def _place_tubules(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2

        positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(self.count)]
        noisy_positions = [(x + random.uniform(-self.noise, self.noise), y + random.uniform(-self.noise, self.noise)) for x, y in positions]

        for x, y in noisy_positions:
            self._subtract_tubule(x, y)

    def _subtract_tubule(self, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        modifier = self.cube.modifiers.new(name=f"Sub_{x}_{y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule

        bpy.context.view_layer.objects.active = self.cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Instantiate and create the tubular structure
creator = TubuleCreator(num_tubules, noise_amount)
creator.create_structure()
