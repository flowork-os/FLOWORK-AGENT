# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_construct_a_cube_of_tubular_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to construct a cube of tubular material.

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total number of tubular elements
tubule_total = 25

class TubularGrid:
    def __init__(self, count):
        self.count = count
        self.cube = None

    def create_base_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        self.cube = bpy.context.object

    def calculate_positions(self):
        grid_dimension = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_dimension
        offset = -1 + spacing / 2
        return [(offset + (i % grid_dimension) * spacing,
                 offset + (i // grid_dimension) * spacing) 
                for i in range(self.count)]

    def add_tubules(self):
        positions = self.calculate_positions()
        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
            tubule = bpy.context.object

            bool_mod = self.cube.modifiers.new(name=f"Tubule_{x}_{y}", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = tubule

            bpy.context.view_layer.objects.active = self.cube
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)

            bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
structure = TubularGrid(tubule_total)
structure.create_base_cube()
structure.add_tubules()
