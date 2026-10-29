# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_for_making_a_model_of_a_tubular_porous_bioinspired_materia" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script for making a model of a tubular porous bioinspired material. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total number of cylindrical tubules
tubule_total = 20

def create_cuboid_with_tubules(tubule_count):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    for i in range(tubule_count):
        x = offset + (i % grid_size) * spacing
        y = offset + (i // grid_size) * spacing
        subtract_tubule(main_cube, x, y)

def subtract_tubule(cube, x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
    tubule = bpy.context.object
    bool_mod = cube.modifiers.new(name=f'Boolean_{x}_{y}', type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = tubule
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    bpy.data.objects.remove(tubule, do_unlink=True)

# Run the creation
create_cuboid_with_tubules(tubule_total)
