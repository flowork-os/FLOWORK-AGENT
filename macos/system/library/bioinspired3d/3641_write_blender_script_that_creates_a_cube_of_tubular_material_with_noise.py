# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_script_that_creates_a_cube_of_tubular_material_with_noise" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender script that creates a cube of tubular material with noise.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Settings for the tubular structure
num_tubules = 12
noise_factor = 0.05

class TubuleCreator:
    def __init__(self, count, noise):
        self.count = count
        self.noise = noise

    def create_tubules(self):
        # Creates a grid of tubules with random noise.
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        base_cube = bpy.context.object
        
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2
        
        positions = [(offset + (i % grid_size) * spacing,
                       offset + (i // grid_size) * spacing)
                      for i in range(self.count)]
        
        noisy_positions = [(x + random.uniform(-self.noise, self.noise),
                            y + random.uniform(-self.noise, self.noise)) for x, y in positions]
        
        for x, y in noisy_positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            
            bool_modifier = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
            bool_modifier.operation = 'DIFFERENCE'
            bool_modifier.object = tubule
            
            bpy.context.view_layer.objects.active = base_cube
            bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Instantiate and create the tubules
creator = TubuleCreator(num_tubules, noise_factor)
creator.create_tubules()
