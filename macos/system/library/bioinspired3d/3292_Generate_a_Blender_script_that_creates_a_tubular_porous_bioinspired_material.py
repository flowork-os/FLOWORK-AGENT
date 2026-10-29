# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_script_that_creates_a_tubular_porous_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender script that creates a tubular porous bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Number of cylindrical elements
tubular_count = 25

class TubularStructure:
    def __init__(self, count):
        self.count = count
        self.base_cube = None

    def create_base(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.base_cube = bpy.context.object

    def generate_tubes(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2
        
        positions = [(start_offset + (i % grid_size) * spacing,
                       start_offset + (i // grid_size) * spacing)
                      for i in range(self.count)]
        
        for x, y in positions:
            self.add_tube(x, y)

    def add_tube(self, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object
        
        modifier = self.base_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tube
        
        bpy.context.view_layer.objects.active = self.base_cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tube, do_unlink=True)

# Instantiate and create the tubular structure
structure = TubularStructure(tubular_count)
structure.create_base()
structure.generate_tubes()
