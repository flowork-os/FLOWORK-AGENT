# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_python_blender_code__make_a_model_of_a_tubular_bioinspired_material_wit" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using python blender code, make a model of a tubular bioinspired material with noise.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

class TubuleGrid:
    def __init__(self, num_tubules=22, noise_factor=0.06):
        self.num_tubules = num_tubules
        self.noise_factor = noise_factor

    def build(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
        grid_dim = math.ceil(math.sqrt(self.num_tubules))
        spacing = 2 / grid_dim
        start = -1 + spacing / 2
        self.create_tubules(cube, grid_dim, spacing, start)

    def create_tubules(self, cube, grid_dim, spacing, start):
        for i in range(self.num_tubules):
            x = start + (i % grid_dim) * spacing
            y = start + (i // grid_dim) * spacing
            x += random.uniform(-self.noise_factor, self.noise_factor)
            y += random.uniform(-self.noise_factor, self.noise_factor)
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            bool_mod = cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = tubule
            bpy.context.view_layer.objects.active = cube
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

tubule_grid = TubuleGrid(num_tubules=19, noise_factor=0.1)
tubule_grid.build()
