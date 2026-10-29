# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_juicer_in_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of juicer in blender script

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

class ModelCreator:
    @staticmethod
    def create_model():
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 1))
        base = bpy.context.object
        base.name = 'Base'
        
        bpy.ops.mesh.primitive_cone_add(radius1=1, radius2=0, depth=1, location=(0, 0, 2.5))
        cone = bpy.context.object
        cone.name = 'Cone'
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=(1, 0, 1))
        spout = bpy.context.object
        spout.name = 'Spout'
        spout.rotation_euler = (0, math.pi / 2, 0)
        
        return base, cone, spout

ModelCreator.create_model()
