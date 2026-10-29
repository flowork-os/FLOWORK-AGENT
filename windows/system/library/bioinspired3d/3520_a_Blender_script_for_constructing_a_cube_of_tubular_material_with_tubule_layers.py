# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_for_constructing_a_cube_of_tubular_material_with_tubule_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script for constructing a cube of tubular material with tubule layers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 25  # Total number of tubules
thickness = 0.03  # Layer thickness

class TubuleCreator:
    def __init__(self, tubule_count, layer_thickness):
        self.tubule_count = tubule_count
        self.layer_thickness = layer_thickness

    def create_structure(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
        grid_size = math.ceil(math.sqrt(self.tubule_count))
        spacing = 2 / grid_size
        start = -1 + spacing / 2
        positions = [(start + (i % grid_size) * spacing, start + (i // grid_size) * spacing) for i in range(self.tubule_count)]
        layers = []

        for x, y in positions:
            self._add_tubule(cube, x, y)

        self._merge_layers(layers)

    def _add_tubule(self, cube, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - self.layer_thickness, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        self._apply_boolean(cube, inner_tubule)
        self._apply_boolean(inner_tubule, outer_tubule)
        bpy.data.objects.remove(outer_tubule, do_unlink=True)

    def _apply_boolean(self, target, obj):
        mod = target.modifiers.new(name="Boolean", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = obj
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.modifier_apply(modifier=mod.name)

    def _merge_layers(self, layers):
        if layers:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in layers:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = layers[0]
            bpy.ops.object.join()
            final_object = bpy.context.object
            final_object.name = "Merged_Layer"

creator = TubuleCreator(num_tubules, thickness)
creator.create_structure()
