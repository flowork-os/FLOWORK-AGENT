# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_code_that_makes_toy_rocket" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender code that makes toy rocket.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def build_rocket():
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=5, location=(0, 0, 2.5))
    rocket_body = bpy.context.object
    rocket_body.name = 'Rocket Body'

    bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(0, 0, 6))
    nose_cone = bpy.context.object
    nose_cone.name = 'Nose Cone'

    for i in range(4):
        angle = math.radians(i * 90)
        x = math.cos(angle) * 1.2
        y = math.sin(angle) * 1.2
        bpy.ops.mesh.primitive_cube_add(size=0.5, location=(x, y, 1))
        fin = bpy.context.object
        fin.scale = (0.1, 1, 0.5)
        fin.rotation_euler = (0, 0, angle)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 1, 5))
    window = bpy.context.object
    window.name = 'Window'

    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1, 0, 2))
    door = bpy.context.object
    door.scale = (0.1, 0.5, 1)
    door.name = 'Door'

    for i in range(3):
        bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.1, location=(0, 0, 1 + i * 2))
        stripe = bpy.context.object
        stripe.name = f'Stripe {i + 1}'
        stripe.scale = (1, 1, 0.05)

build_rocket()
