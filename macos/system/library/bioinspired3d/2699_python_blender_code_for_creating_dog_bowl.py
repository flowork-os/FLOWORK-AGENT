# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_creating_dog_bowl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for creating dog bowl.

import bpy

# Function to clear the mesh objects from the scene

def clear_scene():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

# Clear the scene
clear_scene()

# Create bowl components using a class structure
class Bowl:
    def __init__(self, radius, depth, location, name):
        self.radius = radius
        self.depth = depth
        self.location = location
        self.name = name
        self.create_bowl()

    def create_bowl(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=self.radius, depth=self.depth, location=self.location)
        self.obj = bpy.context.object
        self.obj.name = self.name

# Instantiate the outer and inner bowls
outer_bowl = Bowl(1.5, 0.5, (0, 0, 0), 'BowlOuter')
inner_bowl = Bowl(1.2, 0.4, (0, 0, 0.05), 'BowlInner')

# Apply boolean modifier to create the lip
bool_mod = outer_bowl.obj.modifiers.new(name='BooleanModifier', type='BOOLEAN')
bool_mod.operation = 'DIFFERENCE'
bool_mod.object = inner_bowl.obj
bpy.context.view_layer.objects.active = outer_bowl.obj
bpy.ops.object.modifier_apply(modifier='BooleanModifier')

# Remove the inner bowl from the scene
bpy.data.objects.remove(inner_bowl.obj, do_unlink=True)
