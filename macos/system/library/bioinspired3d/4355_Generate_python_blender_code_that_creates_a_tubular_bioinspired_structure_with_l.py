# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_python_blender_code_that_creates_a_tubular_bioinspired_structure_with_l" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate python blender code that creates a tubular bioinspired structure with layers around each tubule. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tubule_count = 20  # Number of tubules
layer_thickness = 0.06  # Thickness of the surrounding layer

class TubuleGrid:
    def __init__(self, count, thickness):
        self.count = count
        self.thickness = thickness
        self.layers = []

    def create(self):
        cube = self._create_base_cube()
        positions = self._calculate_positions()
        for pos in positions:
            self._add_tubule(cube, pos)
        self._combine_layers()

    def _create_base_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        return bpy.context.object

    def _calculate_positions(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2
        return [(start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing) for i in range(self.count)]

    def _add_tubule(self, cube, position):
        x, y = position
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - self.thickness, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        self._apply_boolean(cube, inner_tubule)
        self._apply_boolean(inner_tubule, outer_tubule)
        bpy.data.objects.remove(outer_tubule, do_unlink=True)

    def _apply_boolean(self, target, obj):
        mod = target.modifiers.new(name="Bool_{0}_{1}".format(obj.location.x, obj.location.y), type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = obj
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.modifier_apply(modifier=mod.name)

    def _combine_layers(self):
        if self.layers:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in self.layers:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = self.layers[0]
            bpy.ops.object.join()
            final_object = bpy.context.object
            final_object.name = "Composite_Layer"

grid = TubuleGrid(tubule_count, layer_thickness)
grid.create()
