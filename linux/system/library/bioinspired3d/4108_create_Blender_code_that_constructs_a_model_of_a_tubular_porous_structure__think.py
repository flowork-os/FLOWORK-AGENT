# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_Blender_code_that_constructs_a_model_of_a_tubular_porous_structure__think" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create Blender code that constructs a model of a tubular porous structure. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the number of cylindrical elements
total_tubes = 20  # Total tubes to create

class TubularStructure:
    def __init__(self, count):
        self.count = count
        self.cube = None

    def create_base_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.cube = bpy.context.object

    def generate_positions(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2
        return [(offset + (i % grid_size) * spacing,
                 offset + (i // grid_size) * spacing)
                for i in range(self.count)]

    def subtract_tubes(self):
        positions = self.generate_positions()
        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tube = bpy.context.object
            mod = self.cube.modifiers.new(name=f"SubtractTube_{x}_{y}", type='BOOLEAN')
            mod.operation = 'DIFFERENCE'
            mod.object = tube
            bpy.context.view_layer.objects.active = self.cube
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(tube, do_unlink=True)

# Create the tubular structure
structure = TubularStructure(total_tubes)
structure.create_base_cube()
structure.subtract_tubes()
