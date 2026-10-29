# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_generates_a_tubular_material_Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that generates a tubular material Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tubule_count = 25

class TubuleCreator:
    def __init__(self, count):
        self.count = count
        self.cube = None

    def create_base_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.cube = bpy.context.object

    def compute_positions(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2
        return [(offset + (i % grid_size) * spacing, 
                 offset + (i // grid_size) * spacing) 
                for i in range(self.count)]

    def add_tubules(self):
        positions = self.compute_positions()
        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object

            bool_mod = self.cube.modifiers.new(name=f"Sub_{x}_{y}", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = tubule

            bpy.context.view_layer.objects.active = self.cube
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

creator = TubuleCreator(tubule_count)
creator.create_base_cube()
creator.add_tubules()
