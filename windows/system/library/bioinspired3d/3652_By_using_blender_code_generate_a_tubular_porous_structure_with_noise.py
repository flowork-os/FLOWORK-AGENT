# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_code_generate_a_tubular_porous_structure_with_noise" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender code generate a tubular porous structure with noise

import bpy
import math
import random

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule parameters
count_of_tubules = 25  # Total tubules
noise_amount = 0.05  # Noise amplitude

class TubuleGrid:
    def __init__(self, count, noise):
        self.count = count
        self.noise = noise

    def build(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
        
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2
        
        positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(self.count)]
        noisy_positions = [(x + random.uniform(-self.noise, self.noise), y + random.uniform(-self.noise, self.noise)) for x, y in positions]
        
        for x, y in noisy_positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            
            boolean_modifier = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
            boolean_modifier.operation = 'DIFFERENCE'
            boolean_modifier.object = tubule
            
            bpy.context.view_layer.objects.active = cube
            bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Create the grid
grid = TubuleGrid(count_of_tubules, noise_amount)
grid.build()
