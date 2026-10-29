# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_to_build_a_model_of_table_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code to build a model of table lamp.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

class Lamp:
    def __init__(self):
        self.create_base()
        self.create_body()
        self.create_shade()
        self.create_switch()

    def create_base(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.05, location=(0, 0, 0))
        self.base = bpy.context.object
        self.base.name = 'Base_Lamp'

    def create_body(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=1, location=(0, 0, 0.5))
        self.body = bpy.context.object
        self.body.name = 'Body_Lamp'

    def create_shade(self):
        bpy.ops.mesh.primitive_cone_add(radius1=0.3, depth=0.7, location=(0, 0, 1.35))
        self.shade = bpy.context.object
        self.shade.name = 'Shade_Lamp'

    def create_switch(self):
        bpy.ops.mesh.primitive_cube_add(size=0.05, location=(0.25, 0, 0.1))
        self.switch = bpy.context.object
        self.switch.name = 'Switch_Lamp'

Lamp()
