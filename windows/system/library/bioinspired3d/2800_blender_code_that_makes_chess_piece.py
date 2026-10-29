# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_makes_chess_piece" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that makes chess piece

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

class ObjectBuilder:
    @staticmethod
    def add_cylinder(radius, height, position, obj_name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
        new_obj = bpy.context.object
        new_obj.name = obj_name
        return new_obj

    @staticmethod
    def add_cone(radius_top, radius_bottom, height, position, obj_name):
        bpy.ops.mesh.primitive_cone_add(radius1=radius_bottom, radius2=radius_top, depth=height, location=position)
        new_cone = bpy.context.object
        new_cone.name = obj_name
        return new_cone

base = ObjectBuilder.add_cylinder(0.75, 0.2, (0, 0, 0.1), 'Base')
body = ObjectBuilder.add_cylinder(0.5, 2.8, (0, 0, 1.5), 'Body')
top = ObjectBuilder.add_cylinder(0.6, 0.2, (0, 0, 2.9), 'Top')
crown = ObjectBuilder.add_cone(0.1, 0.3, 0.5, (0, 0, 3.25), 'Crown')

for z_position in [1.0, 2.0]:
    bpy.ops.mesh.primitive_torus_add(major_radius=0.55, minor_radius=0.05, location=(0, 0, z_position))
    bpy.context.object.name = f'Detail_{z_position}'

bpy.ops.object.select_all(action='DESELECT')
for obj in [base, body, top, crown]:
    obj.select_set(True)

bpy.context.view_layer.objects.active = base
bpy.ops.object.join()

bpy.context.object.scale[2] = 3.75 / bpy.context.object.dimensions.z
bpy.ops.object.transform_apply(scale=True)
