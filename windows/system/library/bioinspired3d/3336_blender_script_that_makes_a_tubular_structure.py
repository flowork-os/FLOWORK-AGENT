# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_makes_a_tubular_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that makes a tubular structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total number of cylindrical elements
total_tubules = 25

class TubuleCreator:
    def __init__(self, count):
        self.count = count

    def create_structure(self):
        self.create_base_cube()
        self.add_tubules()

    def create_base_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.base_cube = bpy.context.object

    def add_tubules(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset_start = -1 + spacing / 2

        positions = [
            (offset_start + (i % grid_size) * spacing,
             offset_start + (i // grid_size) * spacing)
            for i in range(self.count)
        ]

        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            
            modifier = self.base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
            modifier.operation = 'DIFFERENCE'
            modifier.object = tubule
            
            bpy.context.view_layer.objects.active = self.base_cube
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
creator = TubuleCreator(total_tubules)
creator.create_structure()
