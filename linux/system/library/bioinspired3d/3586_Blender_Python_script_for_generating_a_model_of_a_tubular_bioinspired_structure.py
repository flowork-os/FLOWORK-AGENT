# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_for_generating_a_model_of_a_tubular_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script for generating a model of a tubular bioinspired structure with jittered placement.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the structure
tubule_count = 20  # Number of tubules
noise_amount = 0.05  # Noise range

class TubuleCreator:
    def __init__(self, count, noise):
        self.count = count
        self.noise = noise
        self.create_base()

    def create_base(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.base_cube = bpy.context.object
        self.generate_tubules()

    def generate_tubules(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2
        
        positions = [(start_offset + (i % grid_size) * spacing,
                      start_offset + (i // grid_size) * spacing)
                     for i in range(self.count)]
        
        noisy_positions = [(x + random.uniform(-self.noise, self.noise),
                            y + random.uniform(-self.noise, self.noise)) for x, y in positions]
        
        for x, y in noisy_positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            mod = self.base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
            mod.operation = 'DIFFERENCE'
            mod.object = tubule
            bpy.context.view_layer.objects.active = self.base_cube
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Instantiate the creator class
TubuleCreator(tubule_count, noise_amount)
