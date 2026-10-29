# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_blender_code_that_creates_a_tubular_structure_with_noisy_tubule_placement" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a blender code that creates a tubular structure with noisy tubule placement.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

NUM_TUBES = 20  # Total number of tubes to create
NOISE_LEVEL = 0.1  # Maximum positional noise

class TubuleCreator:
    def __init__(self, count, noise):
        self.count = count
        self.noise = noise

    def create_structure(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        base_cube = bpy.context.object
        grid_size = math.ceil(math.sqrt(self.count))
        offset = -1 + (2 / grid_size) / 2
        positions = self.calculate_positions(grid_size, offset)
        self.apply_noise_and_subtract(base_cube, positions)

    def calculate_positions(self, grid_size, offset):
        return [(offset + (i % grid_size) * (2 / grid_size),
                 offset + (i // grid_size) * (2 / grid_size))
                for i in range(self.count)]

    def apply_noise_and_subtract(self, cube, positions):
        for x, y in positions:
            x_noisy = x + random.uniform(-self.noise, self.noise)
            y_noisy = y + random.uniform(-self.noise, self.noise)
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_noisy, y_noisy, 0))
            tubule = bpy.context.object
            bool_mod = cube.modifiers.new(name=f"Subtract_{x_noisy}_{y_noisy}", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = tubule
            bpy.context.view_layer.objects.active = cube
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

creator = TubuleCreator(NUM_TUBES, NOISE_LEVEL)
creator.create_structure()
