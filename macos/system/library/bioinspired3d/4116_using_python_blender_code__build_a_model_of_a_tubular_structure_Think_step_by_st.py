# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_python_blender_code__build_a_model_of_a_tubular_structure_Think_step_by_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using python blender code, build a model of a tubular structure Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 16

class TubuleCreator:
    def __init__(self, count):
        self.count = count

    def create_structure(self):
        self.create_cube()

    def create_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
        self.place_tubules(cube)

    def place_tubules(self, cube):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2

        for i in range(self.count):
            x = start_offset + (i % grid_size) * spacing
            y = start_offset + (i // grid_size) * spacing
            self.subtract_tubule(cube, x, y)

    def subtract_tubule(self, cube, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        modifier = cube.modifiers.new(name=f'Boolean_{x}_{y}', type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

creator = TubuleCreator(num_tubules)
creator.create_structure()
