# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_a_tubular_bioinspired_structure_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of a tubular bioinspired structure using code in Blender

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule configuration
total_tubules = 25

class TubuleCreator:
    def __init__(self, count):
        self.count = count

    def create_structure(self):
        # Main function to create the tubular structure
        self.create_base_cube()
        self.place_tubules()

    def create_base_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.base_cube = bpy.context.object

    def place_tubules(self):
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2

        for i in range(self.count):
            x = offset + (i % grid_size) * spacing
            y = offset + (i // grid_size) * spacing
            self.add_tubule(x, y)

    def add_tubule(self, x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        self.subtract_tubule(tubule)

    def subtract_tubule(self, tubule):
        modifier = self.base_cube.modifiers.new(name='Subtract', type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule
        bpy.context.view_layer.objects.active = self.base_cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Instantiate and create the structure
creator = TubuleCreator(total_tubules)
creator.create_structure()
