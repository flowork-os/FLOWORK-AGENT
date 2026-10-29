# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_bird_feeder_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of bird feeder using blender script

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

class GeometryBuilder:
    @staticmethod
    def create_cylinder(radius, height, position, name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
        obj = bpy.context.object
        obj.name = name

builder = GeometryBuilder()
builder.create_cylinder(0.3, 1, (0, 0, 0.5), 'MainCylinder')
builder.create_cylinder(0.35, 0.05, (0, 0, 0.025), 'SupportBase')

bpy.ops.mesh.primitive_cone_add(radius1=0.4, depth=0.2, location=(0, 0, 1.1))
roof = bpy.context.object
roof.name = 'PyramidRoof'
