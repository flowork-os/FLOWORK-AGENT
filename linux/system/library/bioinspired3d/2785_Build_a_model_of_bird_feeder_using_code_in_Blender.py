# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_bird_feeder_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of bird feeder using code in Blender

import bpy
import math

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a class to encapsulate the model creation
class ModelBuilder:
    def __init__(self):
        self.body = None
        self.roof = None
        self.perch = None

    def add_body(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1.0, location=(0, 0, 0.5))
        self.body = bpy.context.object
        self.body.name = 'MainBody'

    def add_roof(self):
        bpy.ops.mesh.primitive_cone_add(radius1=0.6, depth=0.3, location=(0, 0, 1.15))
        self.roof = bpy.context.object
        self.roof.name = 'RoofCone'

    def add_perch(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.4, location=(0.55, 0, 0.3), rotation=(0, math.pi/2, 0))
        self.perch = bpy.context.object
        self.perch.name = 'Perch'

    def add_opening(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.1, location=(0.5, 0, 0.6))
        opening = bpy.context.object
        opening.name = 'Opening'
        return opening

    def apply_boolean(self, opening):
        bool_mod = self.body.modifiers.new(name='Boolean', type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = opening
        bpy.context.view_layer.objects.active = self.body
        bpy.ops.object.modifier_apply(modifier='Boolean')
        bpy.data.objects.remove(opening, do_unlink=True)

# Create the model
builder = ModelBuilder()
builder.add_body()
builder.add_roof()
builder.add_perch()
opening = builder.add_opening()
builder.apply_boolean(opening)
