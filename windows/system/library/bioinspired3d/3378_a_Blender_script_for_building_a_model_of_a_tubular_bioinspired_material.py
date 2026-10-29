# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_for_building_a_model_of_a_tubular_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script for building a model of a tubular bioinspired material.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular design
total_tubules = 20
ellipse_factor = 1.2
radius_of_tubules = 0.06

class TubuleCreator:
    def __init__(self, count, ellipticity, radius):
        self.count = count
        self.ellipticity = ellipticity
        self.radius = radius

    def create_cube_with_tubules(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2

        positions = [(start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing) for i in range(self.count)]

        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=self.radius, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            tubule.scale[0] *= self.ellipticity
            modifier = cube.modifiers.new(name="Boolean_{0}_{1}".format(x, y), type='BOOLEAN')
            modifier.operation = 'DIFFERENCE'
            modifier.object = tubule
            bpy.context.view_layer.objects.active = cube
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Instantiate and create the structure
creator = TubuleCreator(total_tubules, ellipse_factor, radius_of_tubules)
creator.create_cube_with_tubules()
