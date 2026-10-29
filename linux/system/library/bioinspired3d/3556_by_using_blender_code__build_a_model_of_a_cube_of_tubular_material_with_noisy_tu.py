# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_code__build_a_model_of_a_cube_of_tubular_material_with_noisy_tu" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender code, build a model of a cube of tubular material with noisy tubule placement.

import bpy
import math
import random

# Clear existing objects in the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular formation
total_tubules = 25
max_noise = 0.1

class TubuleGenerator:
    def __init__(self, count, noise):
        self.count = count
        self.noise = noise

    def create_structure(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        base_cube = bpy.context.object
        
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start = -1 + spacing / 2
        
        positions = [(start + (i % grid_size) * spacing, 
                      start + (i // grid_size) * spacing) 
                     for i in range(self.count)]
        
        noisy_positions = [(x + random.uniform(-self.noise, self.noise), 
                            y + random.uniform(-self.noise, self.noise)) for x, y in positions]
        
        for x, y in noisy_positions:
            self.subtract_tubule(base_cube, x, y)

    def subtract_tubule(self, cube, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        bool_mod = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Instantiate and create the tubular structure
generator = TubuleGenerator(total_tubules, max_noise)
generator.create_structure()
