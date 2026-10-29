# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_for_creating_a_model_of_a_cube_of_tubular_bioinspired_material_Thin" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code for creating a model of a cube of tubular bioinspired material Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
count_tubules = 20  # Total number of tubules
stretch_ratio = 1.3  # Factor to stretch tubules into ellipses
radius_tubules = 0.1  # Base radius of the tubules

# Class to handle the tubule creation
class TubuleGrid:
    def __init__(self, count, stretch, radius):
        self.count = count
        self.stretch = stretch
        self.radius = radius

    def create(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        base_cube = bpy.context.object
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start_pos = -1 + spacing / 2

        positions = [(start_pos + (i % grid_size) * spacing,
                      start_pos + (i // grid_size) * spacing)
                     for i in range(self.count)]

        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=self.radius, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            tubule.scale[0] *= self.stretch

            bool_mod = base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = tubule

            bpy.context.view_layer.objects.active = base_cube
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubule structure
grid = TubuleGrid(count_tubules, stretch_ratio, radius_tubules)
grid.create()
