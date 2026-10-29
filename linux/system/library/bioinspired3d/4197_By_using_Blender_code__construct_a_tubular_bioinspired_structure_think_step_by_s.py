# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_code__construct_a_tubular_bioinspired_structure_think_step_by_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender code, construct a tubular bioinspired structure think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total number of tubules to create
num_tubules = 9

class StructureGenerator:
    def __init__(self, count):
        self.count = count
        self.cube = None

    def create_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.cube = bpy.context.object

    def generate_positions(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2
        return [(start_offset + (i % grid_size) * spacing,
                 start_offset + (i // grid_size) * spacing)
                for i in range(self.count)]

    def add_tubules(self):
        positions = self.generate_positions()
        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            self.subtract_tubule(tubule)

    def subtract_tubule(self, tubule):
        modifier = self.cube.modifiers.new(name=f"Boolean_{tubule.location.x}_{tubule.location.y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule
        bpy.context.view_layer.objects.active = self.cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the structure
structure_gen = StructureGenerator(num_tubules)
structure_gen.create_cube()
structure_gen.add_tubules()
