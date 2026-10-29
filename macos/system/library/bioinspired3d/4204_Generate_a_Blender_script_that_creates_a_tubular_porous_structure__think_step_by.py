# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_script_that_creates_a_tubular_porous_structure__think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender script that creates a tubular porous structure. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
num_tubules = 20  # Total number of tubules
ellipse_factor = 1.2  # Factor to stretch tubules into ellipses
radius_of_tubules = 0.06  # Base radius of the tubules

class TubuleCreator:
    def __init__(self, count, ellipticity, radius):
        self.count = count
        self.ellipticity = ellipticity
        self.radius = radius

    def create_structure(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2

        for i in range(self.count):
            x = offset + (i % grid_size) * spacing
            y = offset + (i // grid_size) * spacing
            self.add_tubule(cube, x, y)

    def add_tubule(self, cube, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=self.radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= self.ellipticity

        mod = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = tubule

        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Instantiate and create the structure
creator = TubuleCreator(num_tubules, ellipse_factor, radius_of_tubules)
creator.create_structure()
