# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_Blender_Python_script_that_generates_a_tubular_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make Blender Python script that generates a tubular structure

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular grid
num_tubules = 25
ellipse_ratio = 2.0
base_tubule_radius = 0.1

# Function to build the tubule cube

def build_tubule_cube(tubule_count, ellipse_ratio, tubule_radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    for i in range(tubule_count):
        x = offset + (i % grid_size) * spacing
        y = offset + (i // grid_size) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=tubule_radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipse_ratio
        bool_mod = cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubule structure
build_tubule_cube(num_tubules, ellipse_ratio, base_tubule_radius)
