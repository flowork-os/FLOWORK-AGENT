# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_tubular_bioinspired_structure_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a tubular bioinspired structure in a blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular design
count_of_tubules = 20
stretch_factor = 1.1
base_radius = 0.08

def setup_tubule_structure(count, stretch, radius):
    # Function to build a cube with embedded tubules
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    for i in range(count):
        x = offset + (i % grid_size) * spacing
        y = offset + (i // grid_size) * spacing
        create_tubule(cube, x, y, radius, stretch)

def create_tubule(cube, x, y, radius, stretch):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
    tubule = bpy.context.object
    tubule.scale[0] *= stretch

    bool_mod = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = tubule

    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the setup
setup_tubule_structure(count_of_tubules, stretch_factor, base_radius)
