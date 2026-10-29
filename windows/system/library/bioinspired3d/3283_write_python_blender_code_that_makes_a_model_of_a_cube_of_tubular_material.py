# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_python_blender_code_that_makes_a_model_of_a_cube_of_tubular_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write python blender code that makes a model of a cube of tubular material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set the number of tubules
total_tubules = 20

class TubuleCreator:
    def __init__(self, count):
        self.count = count

    def create_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        return bpy.context.object

    def calculate_positions(self):
        grid_dim = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_dim
        offset = -1 + spacing / 2
        return [(offset + (i % grid_dim) * spacing, offset + (i // grid_dim) * spacing) for i in range(self.count)]

    def create_tubules(self):
        cube = self.create_cube()
        for x, y in self.calculate_positions():
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            mod = cube.modifiers.new(name=f"Difference_{x}_{y}", type='BOOLEAN')
            mod.operation = 'DIFFERENCE'
            mod.object = tubule
            bpy.context.view_layer.objects.active = cube
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

creator = TubuleCreator(total_tubules)
creator.create_tubules()
