# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_blender_code_make_a_model_of_a_tubular_porous_structure__think_step_by_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a blender code make a model of a tubular porous structure. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubule structure
number_of_tubules = 20
elliptical_factor = 1.8
radius_of_tubule = 0.07

class TubuleCreator:
    def __init__(self, count, ellipticity, radius):
        self.count = count
        self.ellipticity = ellipticity
        self.radius = radius

    def create_structure(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        main_cube = bpy.context.object
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2

        for i in range(self.count):
            x = offset + (i % grid_size) * spacing
            y = offset + (i // grid_size) * spacing
            bpy.ops.mesh.primitive_cylinder_add(radius=self.radius, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            tubule.scale[0] *= self.ellipticity
            bool_mod = main_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = tubule
            bpy.context.view_layer.objects.active = main_cube
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Creating the structure
creator = TubuleCreator(number_of_tubules, elliptical_factor, radius_of_tubule)
creator.create_structure()
