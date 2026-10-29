# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_script__build_a_model_of_a_tubular_porous_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender script, build a model of a tubular porous structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Number of cylinders to create
tubule_count = 25

class TubuleCreator:
    def __init__(self, count):
        self.count = count
        self.cube = None

    def create_base_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.cube = bpy.context.object

    def calculate_positions(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2
        return [(offset + (i % grid_size) * spacing,
                 offset + (i // grid_size) * spacing)
                for i in range(self.count)]

    def add_tubules(self):
        positions = self.calculate_positions()
        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            self.subtract_tubule(tubule)

    def subtract_tubule(self, tubule):
        modifier = self.cube.modifiers.new(name=f"Boolean_{tubule.location.x}_{tubule.location.y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule
        bpy.context.view_layer.objects.active = self.cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
creator = TubuleCreator(tubule_count)
creator.create_base_cube()
creator.add_tubules()
