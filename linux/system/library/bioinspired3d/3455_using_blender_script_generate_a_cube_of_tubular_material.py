# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_script_generate_a_cube_of_tubular_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender script generate a cube of tubular material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define parameters for the tubular structure
num_of_tubules = 10  # Total number of tubules
ellipticity_value = 1.3  # Ellipticity for the tubules
radius_of_tubule = 0.08  # Base radius of the tubules

class Tubule:
    def __init__(self, count, ellipticity, radius):
        self.count = count
        self.ellipticity = ellipticity
        self.radius = radius

    def create(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
        grid_size = math.ceil(math.sqrt(self.count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2

        positions = [(offset + (i % grid_size) * spacing, 
                      offset + (i // grid_size) * spacing) 
                     for i in range(self.count)]

        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=self.radius, depth=3, location=(x, y, 0))
            tubule_object = bpy.context.object
            tubule_object.scale[0] *= self.ellipticity
            bool_mod = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = tubule_object
            bpy.context.view_layer.objects.active = cube
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)
            bpy.data.objects.remove(tubule_object, do_unlink=True)

# Create the tubule instance and generate the structure
structure = Tubule(num_of_tubules, ellipticity_value, radius_of_tubule)
structure.create()
