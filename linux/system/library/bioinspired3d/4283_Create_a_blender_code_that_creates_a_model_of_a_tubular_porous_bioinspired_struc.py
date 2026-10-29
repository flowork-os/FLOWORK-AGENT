# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_blender_code_that_creates_a_model_of_a_tubular_porous_bioinspired_struc" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a blender code that creates a model of a tubular porous bioinspired structure. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 20  # Total number of tubules
ellipticity_factor = 2.0  # Stretch factor for the tubules
radius_of_tubule = 0.05  # Radius of each tubule

def create_tubule_grid(total_tubules, ellipticity=1.0, radius=0.1):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    grid_size = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    positions = [(offset + (i % grid_size) * spacing, 
                   offset + (i // grid_size) * spacing) 
                  for i in range(total_tubules)]

    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule_object = bpy.context.object
        tubule_object.scale[0] *= ellipticity
        modifier = cube_object.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule_object
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule_object, do_unlink=True)

create_tubule_grid(num_tubules, ellipticity_factor, radius_of_tubule)
