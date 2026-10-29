# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_code_build_a_model_of_a_tubular_bioinspired_structure_think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender code build a model of a tubular bioinspired structure think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the number of tubules
tubule_number = 20  # Selected number of tubules

class TubuleCreator:
    def __init__(self, count):
        self.count = count

    def create_structure(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
        
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2
        
        positions = [(start_offset + (i % grid_size) * spacing,
                       start_offset + (i // grid_size) * spacing)
                      for i in range(self.count)]
        
        for x, y in positions:
            self.add_tubule(cube, x, y)

    def add_tubule(self, cube, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object

        bool_mod = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Instantiate and create the tubules
creator = TubuleCreator(tubule_number)
creator.create_structure()
