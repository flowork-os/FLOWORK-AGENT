# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_to_make_a_model_of_a_tubular_porous_material_with_random_p" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script to make a model of a tubular porous material with random placement. Think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the structure
num_tubules = 12
noise_level = 0.1

class TubuleCreator:
    def __init__(self, count, noise):
        self.count = count
        self.noise = noise

    def create_structure(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2

        positions = [(offset + (i % grid_size) * spacing,
                      offset + (i // grid_size) * spacing)
                     for i in range(self.count)]

        noisy_positions = [(x + random.uniform(-self.noise, self.noise),
                            y + random.uniform(-self.noise, self.noise))
                           for x, y in positions]

        for x, y in noisy_positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            mod = cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
            mod.operation = 'DIFFERENCE'
            mod.object = tubule
            bpy.context.view_layer.objects.active = cube
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Instantiate and create
creator = TubuleCreator(num_tubules, noise_level)
creator.create_structure()
