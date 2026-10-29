# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_Python_script_make_a_model_of_a_tubular_bioinspired_material_think" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender Python script make a model of a tubular bioinspired material think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule configuration
num_tubules = 20  # Number of tubules
stretch_factor = 1.8  # Ellipticity factor
base_radius = 0.07  # Radius of each tubule

def generate_tubule_positions(count):
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    return [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(count)]

def create_tubules(cube, positions, ellipticity, radius):
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        modifier = cube.modifiers.new(name=f"Tubule_{x}_{y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the main cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.object
positions = generate_tubule_positions(num_tubules)
create_tubules(cube, positions, stretch_factor, base_radius)
