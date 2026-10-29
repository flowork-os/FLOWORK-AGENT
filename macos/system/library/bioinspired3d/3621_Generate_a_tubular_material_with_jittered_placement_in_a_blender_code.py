# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_tubular_material_with_jittered_placement_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a tubular material with jittered placement in a blender code

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule configuration
count_of_tubules = 12
noise_factor = 0.1

class TubuleCreator:
    def __init__(self, count, noise):
        self.count = count
        self.noise = noise

    def create_tubules(self):
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
            modifier = base_cube.modifiers.new(name="Tubule_{:.2f}_{:.2f}".format(x, y), type='BOOLEAN')
            modifier.operation = 'DIFFERENCE'
            modifier.object = tubule
            bpy.context.view_layer.objects.active = base_cube
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubule structure
creator = TubuleCreator(count_of_tubules, noise_factor)
creator.create_tubules()
