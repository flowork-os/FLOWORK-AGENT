# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_dining_table_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate dining table in a Blender script

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a function for the table assembly
class Table:
    def __init__(self, top_size, leg_height, leg_radius):
        self.top_size = top_size
        self.leg_height = leg_height
        self.leg_radius = leg_radius

    def build_top(self):
        bpy.ops.mesh.primitive_cube_add(size=self.top_size, location=(0, 0, 0.75))
        top = bpy.context.object
        top.scale = (1.5, 1, 0.1)
        top.name = 'Table Top'

    def build_legs(self, positions):
        for pos in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=self.leg_radius, depth=self.leg_height, location=(pos[0], pos[1], self.leg_height / 2))
            leg = bpy.context.object
            leg.name = f'Leg_{positions.index(pos) + 1}'

# Instantiate the table
my_table = Table(top_size=2, leg_height=0.7, leg_radius=0.05)
my_table.build_top()
my_table.build_legs([(-1.4, -0.9, 0), (1.4, -0.9, 0), (-1.4, 0.9, 0), (1.4, 0.9, 0)])
