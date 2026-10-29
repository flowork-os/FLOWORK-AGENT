# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_code_in_Blender__make_a_model_of_toy_rocket" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using code in Blender, make a model of toy rocket

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj

rocket_body = create_cylinder(1, 5, (0, 0, 2.5), 'Rocket Body')

bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(0, 0, 6))
nose_cone = bpy.context.object
nose_cone.name = 'Nose Cone'

def create_fin(angle, size, location):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    fin = bpy.context.object
    fin.scale = (0.1, 1, 0.5)
    fin.rotation_euler = (0, 0, angle)

for i in range(4):
    fin_angle = math.radians(i * 90)
    fin_x = math.cos(fin_angle) * 1.2
    fin_y = math.sin(fin_angle) * 1.2
    create_fin(fin_angle, 0.5, (fin_x, fin_y, 1))

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 1, 5))
window = bpy.context.object
window.name = 'Window'

bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1, 0, 2))
door = bpy.context.object
door.scale = (0.1, 0.5, 1)
door.name = 'Door'

for i in range(3):
    create_cylinder(1.05, 0.1, (0, 0, 1 + i * 2), f'Stripe {i + 1}')
    stripe = bpy.context.object
    stripe.scale = (1, 1, 0.05)
