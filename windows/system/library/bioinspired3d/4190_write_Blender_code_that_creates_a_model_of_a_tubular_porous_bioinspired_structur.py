# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_Blender_code_that_creates_a_model_of_a_tubular_porous_bioinspired_structur" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write Blender code that creates a model of a tubular porous bioinspired structure Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the number of tubules
total_tubules = 20  # Total number of tubular structures

class TubuleGrid:
    def __init__(self, tubule_count):
        self.tubule_count = tubule_count

    def create_grid(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        base_cube = bpy.context.object
        
        grid_size = math.ceil(math.sqrt(self.tubule_count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2
        
        positions = [(start_offset + (i % grid_size) * spacing,
                       start_offset + (i // grid_size) * spacing)
                      for i in range(self.tubule_count)]
        
        for x, y in positions:
            self.add_tubule(base_cube, x, y)

    def add_tubule(self, cube, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        modifier = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Generate the tubular structure
grid = TubuleGrid(total_tubules)
grid.create_grid()
