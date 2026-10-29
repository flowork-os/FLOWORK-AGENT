# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_builds_measuring_cup" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that builds measuring cup

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a cup class to encapsulate cup creation
class Cup:
    def __init__(self, radius, height, location):
        self.outer_cup = self.create_cup(radius, height, location)
        self.inner_cup = self.create_cup(radius - 0.1, height, location)
        self.hollow_cup()

    def create_cup(self, radius, height, location):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=location)
        return bpy.context.object

    def hollow_cup(self):
        bool_modifier = self.outer_cup.modifiers.new(type='BOOLEAN', name='Hollow Modifier')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = self.inner_cup
        bpy.context.view_layer.objects.active = self.outer_cup
        bpy.ops.object.modifier_apply(modifier='Hollow Modifier')
        bpy.data.objects.remove(self.inner_cup, do_unlink=True)

# Instantiate the cup
measuring_cup = Cup(1, 2, (0, 0, 1))

# Function to add markings
def add_markings(cup, count):
    for idx in range(1, count + 1):
        bpy.ops.mesh.primitive_plane_add(size=0.1, location=(1.1, 0, idx * 0.4))
        marking = bpy.context.object
        marking.name = f'Marking {idx}'
        marking.rotation_euler[1] = 1.5708  # Rotate for alignment
        marking_bool = cup.outer_cup.modifiers.new(type='BOOLEAN', name=f'Marking Bool {idx}')
        marking_bool.operation = 'DIFFERENCE'
        marking_bool.object = marking
        bpy.context.view_layer.objects.active = cup.outer_cup
        bpy.ops.object.modifier_apply(modifier=f'Marking Bool {idx}')
        bpy.data.objects.remove(marking, do_unlink=True)

# Add measurement markings
add_markings(measuring_cup, 4)
