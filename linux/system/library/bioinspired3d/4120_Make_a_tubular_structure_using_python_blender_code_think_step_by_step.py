# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_tubular_structure_using_python_blender_code_think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a tubular structure using python blender code think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_tubules = 9

class TubuleModel:
    def __init__(self, total):
        self.total = total

    def construct(self):
        base_cube = self.create_cube()
        self.add_tubules(base_cube)

    def create_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        return bpy.context.object

    def add_tubules(self, cube):
        dimension = math.ceil(math.sqrt(self.total))
        gap = 2 / dimension
        initial_position = -1 + gap / 2

        for i in range(self.total):
            x = initial_position + (i % dimension) * gap
            y = initial_position + (i // dimension) * gap
            self.remove_from_cube(cube, x, y)

    def remove_from_cube(self, cube, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        bool_mod = cube.modifiers.new(name=f'Cutout_{x}_{y}', type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

model = TubuleModel(total_tubules)
model.construct()
