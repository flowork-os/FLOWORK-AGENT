# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_code_that_creates_a_cube_of_tubular_bioinspired_material__think_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender code that creates a cube of tubular bioinspired material. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 25
ellipticity_factor = 1.8
base_radius = 0.07

def create_structure(tubule_count, ellipticity, radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    for i in range(tubule_count):
        x = start_offset + (i % grid_size) * spacing
        y = start_offset + (i // grid_size) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        mod = cube.modifiers.new(name=f"Subtraction_{i}", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

create_structure(num_tubules, ellipticity_factor, base_radius)
