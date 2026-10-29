# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_python_code__generate_a_model_of_a_tubular_bioinspired_structur" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender python code, generate a model of a tubular bioinspired structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total number of tubular structures
tubular_count = 25

class TubularStructure:
    def __init__(self, count):
        self.count = count
        self.base_cube = None

    def create_base_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.base_cube = bpy.context.object

    def generate_tubes(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2

        for i in range(self.count):
            x = start_offset + (i % grid_size) * spacing
            y = start_offset + (i // grid_size) * spacing
            self.add_tube(x, y)

    def add_tube(self, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object
        mod = self.base_cube.modifiers.new(name='SubtractTube', type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = tube
        bpy.context.view_layer.objects.active = self.base_cube
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(tube, do_unlink=True)

# Create and execute the tubular structure
structure = TubularStructure(tubular_count)
structure.create_base_cube()
structure.generate_tubes()
