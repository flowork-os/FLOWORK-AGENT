# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_Blender_code_that_makes_a_cube_of_tubular_bioinspired_material_with_noi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a Blender code that makes a cube of tubular bioinspired material with noisy tubule placement think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_tubules = 20  # Number of tubules to create
noise_variation = 0.1  # Noise range for positioning

class TubularStructure:
    def __init__(self, tubule_count, noise):
        self.tubule_count = tubule_count
        self.noise = noise

    def create_structure(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        base_cube = bpy.context.object
        
        grid_dim = math.ceil(math.sqrt(self.tubule_count))
        spacing = 2 / grid_dim
        start_offset = -1 + spacing / 2
        
        positions = [(start_offset + (i % grid_dim) * spacing, start_offset + (i // grid_dim) * spacing) for i in range(self.tubule_count)]
        noisy_positions = [(x + random.uniform(-self.noise, self.noise), y + random.uniform(-self.noise, self.noise)) for x, y in positions]
        
        for x, y in noisy_positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            
            boolean_mod = base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
            boolean_mod.operation = 'DIFFERENCE'
            boolean_mod.object = tubule
            
            bpy.context.view_layer.objects.active = base_cube
            bpy.ops.object.modifier_apply(modifier=boolean_mod.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

structure = TubularStructure(total_tubules, noise_variation)
structure.create_structure()
