# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_code_in_Blender__construct_a_tubular_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With code in Blender, construct a tubular bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular assembly
total_tubules = 25  # Number of tubules
ellipse_factor = 1.2  # Factor for stretching tubules
radius_of_tubules = 0.05  # Radius of each tubule

class TubuleCreator:
    def __init__(self, count, ellipticity, radius):
        self.count = count
        self.ellipticity = ellipticity
        self.radius = radius

    def create(self):
        self._initialize_cube()
        self._generate_tubules()

    def _initialize_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.cube = bpy.context.object

    def _generate_tubules(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2

        for i in range(self.count):
            x = start_offset + (i % grid_size) * spacing
            y = start_offset + (i // grid_size) * spacing
            self._add_tubule(x, y)

    def _add_tubule(self, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=self.radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= self.ellipticity

        modifier = self.cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule

        bpy.context.view_layer.objects.active = self.cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Instantiate and create the tubular structure
creator = TubuleCreator(total_tubules, ellipse_factor, radius_of_tubules)
creator.create()
