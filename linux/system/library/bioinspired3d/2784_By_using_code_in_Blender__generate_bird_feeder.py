# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_code_in_Blender__generate_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using code in Blender, generate bird feeder

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_cylinder(radius, depth, location, rotation=(0, 0, 0), name='Cylinder'):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return obj

body_cylinder = create_cylinder(0.5, 1.0, (0, 0, 0.5), name='MainBody')

bpy.ops.mesh.primitive_cone_add(radius1=0.6, depth=0.3, location=(0, 0, 1.15))
roof_cone = bpy.context.object
roof_cone.name = 'RoofCone'

perch_cylinder = create_cylinder(0.05, 0.4, (0.55, 0, 0.3), rotation=(0, math.pi/2, 0), name='PerchCylinder')

opening_cylinder = create_cylinder(0.15, 0.1, (0.5, 0, 0.6), name='OpeningCylinder')

bool_modifier = body_cylinder.modifiers.new(name='BooleanModifier', type='BOOLEAN')
bool_modifier.operation = 'DIFFERENCE'
bool_modifier.object = opening_cylinder
bpy.context.view_layer.objects.active = body_cylinder
bpy.ops.object.modifier_apply(modifier='BooleanModifier')

bpy.data.objects.remove(opening_cylinder, do_unlink=True)
