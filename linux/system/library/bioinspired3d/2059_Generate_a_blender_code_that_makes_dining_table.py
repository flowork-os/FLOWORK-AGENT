# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_blender_code_that_makes_dining_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a blender code that makes dining table.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

class Table:
    def __init__(self, top_scale, leg_height, leg_radius):
        self.top_scale = top_scale
        self.leg_height = leg_height
        self.leg_radius = leg_radius

    def create_table_top(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.75))
        table_top = bpy.context.object
        table_top.name = 'Table Surface'
        table_top.scale = self.top_scale

    def create_leg(self, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=self.leg_radius, depth=self.leg_height, location=(x, y, self.leg_height / 2))
        leg = bpy.context.object
        leg.name = 'Leg'

my_table = Table(top_scale=(1.5, 0.9, 0.05), leg_height=0.7, leg_radius=0.05)
my_table.create_table_top()

leg_coordinates = [(-1.4, -0.8), (1.4, -0.8), (-1.4, 0.8), (1.4, 0.8)]
for coord in leg_coordinates:
    my_table.create_leg(*coord)
