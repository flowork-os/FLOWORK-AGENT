# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_to_construct_a_tubular_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code to construct a tubular bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule parameters
num_tubules_total = 25  # Total number of tubules
ellipticity_factor = 1.1  # Factor to stretch tubules
base_tubule_radius = 0.06  # Base radius of tubules

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
        start_offset = -1 + spacing / 2
        positions = [(start_offset + (i % grid_size) * spacing, 
                      start_offset + (i // grid_size) * spacing) 
                     for i in range(self.count)]
        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=self.radius, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            tubule.scale[0] *= self.ellipticity
            bool_mod = main_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = tubule
            bpy.context.view_layer.objects.active = main_cube
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Instantiate and create the tubule structure
creator = TubuleCreator(num_tubules_total, ellipticity_factor, base_tubule_radius)
creator.create_structure()
