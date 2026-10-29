# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_blender_code_that_builds_a_cube_of_tubular_material__Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a blender code that builds a cube of tubular material. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the parameters for the structure
num_tubules = 12
ellipticity_factor = 1.8
base_tubule_radius = 0.08

class TubuleCreator:
    def __init__(self, count, ellipticity, radius):
        self.count = count
        self.ellipticity = ellipticity
        self.radius = radius

    def create_tubule_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2

        positions = [(start_offset + (i % grid_size) * spacing,
                      start_offset + (i // grid_size) * spacing)
                     for i in range(self.count)]

        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=self.radius, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            tubule.scale[0] *= self.ellipticity

            modifier = cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
            modifier.operation = 'DIFFERENCE'
            modifier.object = tubule

            bpy.context.view_layer.objects.active = cube
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
creator = TubuleCreator(num_tubules, ellipticity_factor, base_tubule_radius)
creator.create_tubule_cube()
