# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_blender_python_code_that_constructs_a_model_of_a_tubular_material_with_jitt" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make blender python code that constructs a model of a tubular material with jittered placement think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular model
tube_count = 20  # Total number of tubes
jitter_amount = 0.05  # Noise applied to positions

class TubuleCreator:
    def __init__(self, count, noise):
        self.count = count
        self.noise = noise

    def create(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        main_cube = bpy.context.object
        grid_dim = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_dim
        offset = -1 + spacing / 2

        positions = [(offset + (i % grid_dim) * spacing, 
                      offset + (i // grid_dim) * spacing)
                     for i in range(self.count)]

        noisy_positions = [(x + random.uniform(-self.noise, self.noise), 
                            y + random.uniform(-self.noise, self.noise)) for x, y in positions]

        for x, y in noisy_positions:
            self.subtract_tubule(main_cube, x, y)

    def subtract_tubule(self, cube, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object

        bool_mod = cube.modifiers.new(name="Subtract_{:.2f}_{:.2f}".format(x, y), type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tube

        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        bpy.data.objects.remove(tube, do_unlink=True)

# Instantiate and create the tubules
creator = TubuleCreator(tube_count, jitter_amount)
creator.create()
