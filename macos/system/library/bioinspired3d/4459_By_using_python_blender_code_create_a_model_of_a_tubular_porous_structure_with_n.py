# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_python_blender_code_create_a_model_of_a_tubular_porous_structure_with_n" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using python blender code create a model of a tubular porous structure with noisy tubule placement. think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the structure
total_tubules = 20  # Number of tubules in the grid
max_noise = 0.1  # Noise range for positioning

class TubuleCreator:
    def __init__(self, count, noise):
        self.count = count
        self.noise = noise

    def create(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
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
            modifier = cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
            modifier.operation = 'DIFFERENCE'
            modifier.object = tubule
            bpy.context.view_layer.objects.active = cube
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the creation
creator = TubuleCreator(total_tubules, max_noise)
creator.create()
