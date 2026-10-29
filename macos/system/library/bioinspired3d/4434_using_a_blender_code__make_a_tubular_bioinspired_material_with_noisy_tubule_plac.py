# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_blender_code__make_a_tubular_bioinspired_material_with_noisy_tubule_plac" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a blender code, make a tubular bioinspired material with noisy tubule placement Think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the structure
num_tubules = 20  # Total number of tubules
max_noise = 0.05  # Noise deviation

class TubuleCreator:
    def __init__(self, count, noise):
        self.count = count
        self.noise = noise

    def create_structure(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        base_cube = bpy.context.object
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start = -1 + spacing / 2

        positions = [(start + (i % grid_size) * spacing,
                      start + (i // grid_size) * spacing)
                     for i in range(self.count)]

        noisy_positions = [(x + random.uniform(-self.noise, self.noise),
                            y + random.uniform(-self.noise, self.noise)) for x, y in positions]

        for x, y in noisy_positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            modifier = base_cube.modifiers.new(name="BooleanModifier", type='BOOLEAN')
            modifier.operation = 'DIFFERENCE'
            modifier.object = tubule
            bpy.context.view_layer.objects.active = base_cube
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Instantiate and create
creator = TubuleCreator(num_tubules, max_noise)
creator.create_structure()
