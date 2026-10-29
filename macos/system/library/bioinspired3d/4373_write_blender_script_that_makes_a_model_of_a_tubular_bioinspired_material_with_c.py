# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_script_that_makes_a_model_of_a_tubular_bioinspired_material_with_c" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender script that makes a model of a tubular bioinspired material with cortical layers think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular framework
total_tubules = 12  # Total number of tubules
shell_width = 0.04  # Width of the layer around each tubule

class TubuleCreator:
    def __init__(self, tubule_count, thickness):
        self.tubule_count = tubule_count
        self.thickness = thickness

    def create(self):
        self.create_cube()
        self.arrange_tubules()

    def create_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.base_cube = bpy.context.object

    def arrange_tubules(self):
        grid_size = math.ceil(math.sqrt(self.tubule_count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2

        positions = [(start_offset + (i % grid_size) * spacing,
                      start_offset + (i // grid_size) * spacing)
                     for i in range(self.tubule_count)]

        for x, y in positions:
            self.create_tubule(x, y)

    def create_tubule(self, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - self.thickness, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object

        self.apply_boolean(inner_tubule, outer_tubule)

    def apply_boolean(self, inner, outer):
        bool_mod = self.base_cube.modifiers.new(name="Boolean_Subtract", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner
        bpy.context.view_layer.objects.active = self.base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        layer_mod = inner.modifiers.new(name="Layer_Bool", type='BOOLEAN')
        layer_mod.operation = 'DIFFERENCE'
        layer_mod.object = outer
        bpy.context.view_layer.objects.active = inner
        bpy.ops.object.modifier_apply(modifier=layer_mod.name)

        bpy.data.objects.remove(outer, do_unlink=True)

# Instantiate and create the tubular structure
creator = TubuleCreator(total_tubules, shell_width)
creator.create()
