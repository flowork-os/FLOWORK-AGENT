# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_that_generates_a_model_of_a_tubular_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code that generates a model of a tubular bioinspired structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total tubules in the grid
total_tubules = 25  # Total number of tubules

class TubuleGrid:
    def __init__(self, count):
        self.count = count

    def create(self):
        self.make_cube()

    def make_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
        self.create_tubules(cube)

    def create_tubules(self, cube):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2
        
        positions = [(start_offset + (i % grid_size) * spacing, 
                      start_offset + (i // grid_size) * spacing) 
                     for i in range(self.count)]
        
        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            
            modifier = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
            modifier.operation = 'DIFFERENCE'
            modifier.object = tubule
            
            bpy.context.view_layer.objects.active = cube
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubule grid
grid = TubuleGrid(total_tubules)
grid.create()
