# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_tubular_porous_bioinspired_material_in_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a tubular porous bioinspired material in Blender Python script

import bpy
import math

# Clear the current scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the parameters
total_tubules = 20
ellipse_factor = 1.2
tube_radius = 0.06

class TubuleCube:
    def __init__(self, count, ellipticity, radius):
        self.count = count
        self.ellipticity = ellipticity
        self.radius = radius
        self.cube = None

    def create_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.cube = bpy.context.object

    def generate_positions(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2
        return [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(self.count)]

    def add_tubules(self):
        positions = self.generate_positions()
        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=self.radius, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            tubule.scale[0] *= self.ellipticity
            bool_mod = self.cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = tubule
            bpy.context.view_layer.objects.active = self.cube
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Create and configure the tubule cube
structure = TubuleCube(total_tubules, ellipse_factor, tube_radius)
structure.create_cube()
structure.add_tubules()
