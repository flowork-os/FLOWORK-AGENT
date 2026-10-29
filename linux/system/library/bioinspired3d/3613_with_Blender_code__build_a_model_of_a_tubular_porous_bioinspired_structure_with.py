# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_Blender_code__build_a_model_of_a_tubular_porous_bioinspired_structure_with" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with Blender code, build a model of a tubular porous bioinspired structure with random placement.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure configuration
count_tubules = 18  # Number of tubules
noise_variation = 0.07  # Noise deviation

class TubuleModel:
    def __init__(self, count, noise):
        self.count = count
        self.noise = noise

    def build(self):
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
            self._create_tubule(base_cube, x, y)

    def _create_tubule(self, cube, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        bool_mod = cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Instantiate and build the model
model = TubuleModel(count_tubules, noise_variation)
model.build()
