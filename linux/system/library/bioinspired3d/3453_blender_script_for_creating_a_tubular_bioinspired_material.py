# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_creating_a_tubular_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for creating a tubular bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule structure parameters
count_tubules = 25  # Number of tubules in the structure
ellipse_ratio = 1.2  # Ellipticity factor for the tubules
radius_tubule = 0.1  # Radius of the tubules

class TubuleCreator:
    def __init__(self, count, ellipticity, radius):
        self.count = count
        self.ellipticity = ellipticity
        self.radius = radius

    def create_tubule_cube(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
        grid_dim = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_dim
        offset = -1 + spacing / 2

        positions = [(offset + (i % grid_dim) * spacing, 
                      offset + (i // grid_dim) * spacing) 
                     for i in range(self.count)]

        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=self.radius, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            tubule.scale[0] *= self.ellipticity
            bool_mod = cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = tubule
            bpy.context.view_layer.objects.active = cube
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)
            bpy.data.objects.remove(tubule, do_unlink=True)

# Instantiate and create the structure
creator = TubuleCreator(count_tubules, ellipse_ratio, radius_tubule)
creator.create_tubule_cube()
