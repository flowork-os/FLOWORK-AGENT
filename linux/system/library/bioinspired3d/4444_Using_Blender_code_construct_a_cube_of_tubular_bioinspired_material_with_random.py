# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_Blender_code_construct_a_cube_of_tubular_bioinspired_material_with_random" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using Blender code construct a cube of tubular bioinspired material with random placement. think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular model
total_tubules = 12  # Number of tubules in the model
noise_amount = 0.05  # Max deviation for noise

class TubuleCreator:
    def __init__(self, count, noise):
        self.count = count
        self.noise = noise

    def create(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        base_cube = bpy.context.object
        
        grid_dim = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_dim
        offset = -1 + spacing / 2
        
        positions = [(offset + (i % grid_dim) * spacing,
                      offset + (i // grid_dim) * spacing)
                     for i in range(self.count)]
        
        for pos in positions:
            x = pos[0] + random.uniform(-self.noise, self.noise)
            y = pos[1] + random.uniform(-self.noise, self.noise)
            self._add_tubule(base_cube, x, y)

    def _add_tubule(self, cube, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        bool_mod = cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create and execute the TubuleCreator
creator = TubuleCreator(total_tubules, noise_amount)
creator.create()
