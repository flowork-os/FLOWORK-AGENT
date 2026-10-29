# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_toy_rocket_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of toy rocket in code in Blender

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

class Rocket:
    def __init__(self):
        self.create_body()
        self.create_nose_cone()
        self.create_fins()
        self.create_window()
        self.create_door()
        self.add_stripes()

    def create_body(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=5, location=(0, 0, 2.5))
        self.body = bpy.context.object
        self.body.name = 'Rocket Body'

    def create_nose_cone(self):
        bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(0, 0, 6))
        self.nose = bpy.context.object
        self.nose.name = 'Nose Cone'

    def create_fins(self):
        for i in range(4):
            angle = math.radians(i * 90)
            x = math.cos(angle) * 1.2
            y = math.sin(angle) * 1.2
            bpy.ops.mesh.primitive_cube_add(size=0.5, location=(x, y, 1))
            fin = bpy.context.object
            fin.scale = (0.1, 1, 0.5)
            fin.rotation_euler = (0, 0, angle)

    def create_window(self):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 1, 5))
        self.window = bpy.context.object
        self.window.name = 'Window'

    def create_door(self):
        bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1, 0, 2))
        self.door = bpy.context.object
        self.door.scale = (0.1, 0.5, 1)
        self.door.name = 'Door'

    def add_stripes(self):
        for i in range(3):
            bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.1, location=(0, 0, 1 + i * 2))
            stripe = bpy.context.object
            stripe.name = f'Stripe {i + 1}'
            stripe.scale = (1, 1, 0.05)

rocket = Rocket()
