# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_python_blender_code_that_creates_a_model_of_mri_machine" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate python blender code that creates a model of mri machine.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the MRI machine using an object-oriented approach
class MRIMachine:
    def __init__(self):
        self.main_part = self.create_cylinder(1.5, 2, (0, 0, 0), 'MRI Body')
        self.create_opening(1, 2.2)
        self.add_control_panel((1.75, 0, 0.75))

    def create_cylinder(self, radius, depth, location, name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        obj = bpy.context.object
        obj.name = name
        return obj

    def create_opening(self, radius, depth):
        opening = self.create_cylinder(radius, depth, (0, 0, 0), 'Circular Opening')
        bool_modifier = self.main_part.modifiers.new(name='Cutout', type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = opening
        bpy.context.view_layer.objects.active = self.main_part
        bpy.ops.object.modifier_apply(modifier='Cutout')
        bpy.data.objects.remove(opening, do_unlink=True)

    def add_control_panel(self, location):
        bpy.ops.mesh.primitive_cube_add(size=0.5, location=location)
        control_panel = bpy.context.object
        control_panel.name = 'Control Panel'

# Instantiate the MRI machine
mri_machine = MRIMachine()
