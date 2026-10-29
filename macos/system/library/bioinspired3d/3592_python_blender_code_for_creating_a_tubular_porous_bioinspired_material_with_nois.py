# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_creating_a_tubular_porous_bioinspired_material_with_nois" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for creating a tubular porous bioinspired material with noisy tubule placement

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
num_tubules = 12  # Number of tubules
noise_amount = 0.1  # Noise amount for position variation

class TubularStructure:
    def __init__(self, count, noise):
        self.count = count
        self.noise = noise

    def create(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
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
            boolean_mod = cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
            boolean_mod.operation = 'DIFFERENCE'
            boolean_mod.object = tubule
            bpy.context.view_layer.objects.active = cube
            bpy.ops.object.modifier_apply(modifier=boolean_mod.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
structure = TubularStructure(num_tubules, noise_amount)
structure.create()
