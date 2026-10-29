# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_tubular_bioinspired_material_using_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a tubular bioinspired material using a Blender script

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the structure
count_of_tubules = 18
stretch_factor = 1.4
base_radius = 0.06

class TubuleGrid:
    def __init__(self, count, stretch, radius):
        self.count = count
        self.stretch = stretch
        self.radius = radius

    def build(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2

        positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(self.count)]

        for x, y in positions:
            self.add_tubule(cube, x, y)

    def add_tubule(self, cube, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=self.radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= self.stretch
        modifier = cube.modifiers.new(name=f'Boolean_{x}_{y}', type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubule grid
tubule_grid = TubuleGrid(count_of_tubules, stretch_factor, base_radius)
tubule_grid.build()
