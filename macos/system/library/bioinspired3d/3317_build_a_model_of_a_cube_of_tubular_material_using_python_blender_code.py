# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_a_cube_of_tubular_material_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of a cube of tubular material using python blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Number of tubules to create
tubule_total = 25

class TubularGrid:
    def __init__(self, count):
        self.count = count

    def build_structure(self):
        self.create_cube()
        self.place_tubules()

    def create_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.cube = bpy.context.object

    def place_tubules(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2

        positions = [(start_offset + (i % grid_size) * spacing,
                      start_offset + (i // grid_size) * spacing)
                     for i in range(self.count)]

        for x, y in positions:
            self.add_tubule(x, y)

    def add_tubule(self, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object

        bool_mod = self.cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule

        bpy.context.view_layer.objects.active = self.cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular grid
grid = TubularGrid(tubule_total)
grid.build_structure()
