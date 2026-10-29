# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_tubular_material_with_cortical_layers_using_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a tubular material with cortical layers using a Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular structure
num_tubules = 16  # Total number of tubules
layer_thickness = 0.04  # Thickness of layer around each tubule

class TubuleCreator:
    def __init__(self, count, thickness):
        self.count = count
        self.thickness = thickness
        self.cube = None
        self.layer_objects = []

    def setup_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.cube = bpy.context.object

    def create_tubules(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2

        for i in range(self.count):
            x = start_offset + (i % grid_size) * spacing
            y = start_offset + (i // grid_size) * spacing
            self.create_tubule(x, y)

    def create_tubule(self, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - self.thickness, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object

        self.apply_boolean(self.cube, inner_tubule)
        self.apply_boolean(inner_tubule, outer_tubule)
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        self.layer_objects.append(inner_tubule)

    def apply_boolean(self, target, obj):
        modifier = target.modifiers.new(name='Boolean', type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = obj
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.modifier_apply(modifier=modifier.name)

    def finalize(self):
        if self.layer_objects:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in self.layer_objects:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = self.layer_objects[0]
            bpy.ops.object.join()
            layer_shell = bpy.context.object
            layer_shell.name = 'Layer_Shell'

# Create the structure
creator = TubuleCreator(num_tubules, layer_thickness)
creator.setup_cube()
creator.create_tubules()
creator.finalize()
