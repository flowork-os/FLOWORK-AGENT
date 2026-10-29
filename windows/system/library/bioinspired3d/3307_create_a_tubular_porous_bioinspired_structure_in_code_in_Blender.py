# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_tubular_porous_bioinspired_structure_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a tubular porous bioinspired structure in code in Blender

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total number of tubular elements
tubular_count = 25

class TubularStructure:
    def __init__(self, count):
        self.count = count

    def create_structure(self):
        cube = self._create_base_cube()
        positions = self._calculate_positions()
        self._subtract_tubules(cube, positions)

    def _create_base_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        return bpy.context.object

    def _calculate_positions(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2
        return [(start_offset + (i % grid_size) * spacing,
                 start_offset + (i // grid_size) * spacing)
                for i in range(self.count)]

    def _subtract_tubules(self, cube, positions):
        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            mod = cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
            mod.operation = 'DIFFERENCE'
            mod.object = tubule
            bpy.context.view_layer.objects.active = cube
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Create and execute the tubular structure
structure = TubularStructure(tubular_count)
structure.create_structure()
