# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_a_tubular_porous_bioinspired_structure_with_noisy_tubule_placem" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of a tubular porous bioinspired structure with noisy tubule placement in a Blender code

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular structure
total_tubules = 20  # Number of tubules
jitter_amount = 0.05  # Max noise for positions

class TubuleGenerator:
    def __init__(self, count, noise):
        self.count = count
        self.noise = noise
        
    def create_structure(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        base_cube = bpy.context.object
        
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2
        
        positions = [(start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing) for i in range(self.count)]
        noisy_positions = [(x + random.uniform(-self.noise, self.noise), y + random.uniform(-self.noise, self.noise)) for x, y in positions]
        
        for x, y in noisy_positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            
            bool_mod = base_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = tubule
            
            bpy.context.view_layer.objects.active = base_cube
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Create tubules
generator = TubuleGenerator(total_tubules, jitter_amount)
generator.create_structure()
