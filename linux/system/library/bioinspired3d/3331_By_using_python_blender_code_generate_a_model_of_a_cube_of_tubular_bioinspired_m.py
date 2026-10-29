# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_python_blender_code_generate_a_model_of_a_cube_of_tubular_bioinspired_m" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using python blender code generate a model of a cube of tubular bioinspired material.

import bpy
import math

# Clear existing objects in the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the number of tubes
total_tubes = 12

class TubularGrid:
    def __init__(self, tube_count):
        self.tube_count = tube_count
        self.cube = None

    def create_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.cube = bpy.context.object

    def calculate_positions(self):
        grid_size = math.ceil(math.sqrt(self.tube_count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2
        return [(start_offset + (i % grid_size) * spacing,
                 start_offset + (i // grid_size) * spacing)
                for i in range(self.tube_count)]

    def create_tubes(self):
        positions = self.calculate_positions()
        for pos in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos[0], pos[1], 0))
            tube = bpy.context.object
            bool_mod = self.cube.modifiers.new(name=f"Cut_{pos[0]}_{pos[1]}", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = tube
            bpy.context.view_layer.objects.active = self.cube
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)
            bpy.data.objects.remove(tube, do_unlink=True)

# Create and execute tubular grid
grid = TubularGrid(total_tubes)
grid.create_cube()
grid.create_tubes()
