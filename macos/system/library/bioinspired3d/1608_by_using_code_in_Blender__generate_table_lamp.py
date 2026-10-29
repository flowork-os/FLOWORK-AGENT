# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_code_in_Blender__generate_table_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using code in Blender, generate table lamp

import bpy
import math

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Object-oriented approach to create a lamp
class Lamp:
    def __init__(self):
        self.base = self.create_part(1, 0.2, (0, 0, 0.1), 'Lamp_Base')
        self.pole = self.create_part(0.1, 3, (0, 0, 1.6), 'Lamp_Pole')
        self.lampshade = self.create_part(0.8, 1, (0, 0, 3.6), 'Lamp_Lampshade')
        self.pull_chain = self.create_part(0.02, 1.5, (0.1, 0, 2.25), 'Lamp_Pull_Chain')
        self.pull_chain.rotation_euler = (0, 0, math.radians(90))

    def create_part(self, radius, depth, location, name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        part = bpy.context.object
        part.name = name
        return part

# Instantiate the lamp
lamp = Lamp()
