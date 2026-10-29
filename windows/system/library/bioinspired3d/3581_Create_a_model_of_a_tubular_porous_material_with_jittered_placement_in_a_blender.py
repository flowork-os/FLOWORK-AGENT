# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_a_tubular_porous_material_with_jittered_placement_in_a_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of a tubular porous material with jittered placement in a blender code

import bpy
import math
import random

# Clear the current scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
total_tubules = 25  # Number of tubules
jitter_amount = 0.05  # Noise factor for positioning

class TubuleCreator:
    def __init__(self, count, noise):
        self.count = count
        self.noise = noise
        self.base_cube = None

    def create_base_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.base_cube = bpy.context.object

    def generate_positions(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2
        
        return [(start_offset + (i % grid_size) * spacing,
                 start_offset + (i // grid_size) * spacing)
                for i in range(self.count)]

    def apply_noise(self, positions):
        return [(x + random.uniform(-self.noise, self.noise),
                 y + random.uniform(-self.noise, self.noise))
                for x, y in positions]

    def subtract_tubules(self, positions):
        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            
            modifier = self.base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
            modifier.operation = 'DIFFERENCE'
            modifier.object = tubule
            
            bpy.context.view_layer.objects.active = self.base_cube
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

    def create_tubular_structure(self):
        self.create_base_cube()
        positions = self.generate_positions()
        noisy_positions = self.apply_noise(positions)
        self.subtract_tubules(noisy_positions)

# Instantiate and create the structure
creator = TubuleCreator(total_tubules, jitter_amount)
creator.create_tubular_structure()
