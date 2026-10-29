# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_for_building_a_model_of_a_tubular_porous_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code for building a model of a tubular porous structure.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular model parameters
num_tubules = 20  # Number of tubules
ellipticity_factor = 1.2  # Stretching factor for the tubules
radius_of_tubule = 0.06  # Radius for the tubules

class TubuleCreator:
    def __init__(self, tubule_count, ellipticity, radius):
        self.tubule_count = tubule_count
        self.ellipticity = ellipticity
        self.radius = radius

    def create_tubule_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
        grid_size = math.ceil(math.sqrt(self.tubule_count))
        spacing = 2 / grid_size
        start_offset = -1 + spacing / 2

        for i in range(self.tubule_count):
            x = start_offset + (i % grid_size) * spacing
            y = start_offset + (i // grid_size) * spacing
            bpy.ops.mesh.primitive_cylinder_add(radius=self.radius, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            tubule.scale[0] *= self.ellipticity
            self.apply_boolean(cube, tubule)

    def apply_boolean(self, cube, tubule):
        modifier = cube.modifiers.new(name=f"Bool_{tubule.name}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Instantiate and create the structure
creator = TubuleCreator(num_tubules, ellipticity_factor, radius_of_tubule)
creator.create_tubule_cube()
