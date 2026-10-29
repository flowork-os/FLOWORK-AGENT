# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_Blender_script_generate_a_tubular_porous_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a Blender script generate a tubular porous structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular model
num_tubules = 18  # Total number of tubules
ellipse_scale = 1.4  # Factor to stretch tubules into ellipses
radius_of_tubules = 0.09  # Base radius of the tubules

# Function to create a grid of tubules
def generate_tubule_structure(tubule_count, ellipticity, radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2

    for i in range(tubule_count):
        x = start_offset + (i % grid_size) * spacing
        y = start_offset + (i // grid_size) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity

        modifier = base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
generate_tubule_structure(num_tubules, ellipse_scale, radius_of_tubules)
