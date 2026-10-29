# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_that_creates_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code that creates coffee table.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

class Table:
    def __init__(self):
        self.top_size = (1.5, 0.75, 0.1)
        self.leg_height = 0.5
        self.leg_radius = 0.05
        self.create_table()

    def create_table(self):
        self.create_table_top()
        self.create_legs()

    def create_table_top(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
        top = bpy.context.object
        top.name = 'Table Surface'
        top.scale = self.top_size

    def create_legs(self):
        positions = [(-1.4, -0.7, self.leg_height / 2), (1.4, -0.7, self.leg_height / 2), (-1.4, 0.7, self.leg_height / 2), (1.4, 0.7, self.leg_height / 2)]
        for i, pos in enumerate(positions):
            bpy.ops.mesh.primitive_cylinder_add(radius=self.leg_radius, depth=self.leg_height, location=pos)
            leg = bpy.context.object
            leg.name = f'Leg {i + 1}'

Table()
