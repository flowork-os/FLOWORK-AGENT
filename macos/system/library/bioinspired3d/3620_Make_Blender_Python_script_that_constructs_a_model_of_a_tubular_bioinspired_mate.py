# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_Blender_Python_script_that_constructs_a_model_of_a_tubular_bioinspired_mate" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make Blender Python script that constructs a model of a tubular bioinspired material with noise.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Structure parameters
total_tubules = 20  # Number of tubules to create
noise_variation = 0.05  # Noise range for positioning

def create_structure(tubule_count, noise):
    # Main function to construct the tubule grid
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    dimension = math.ceil(math.sqrt(tubule_count))
    separation = 2 / dimension
    start_point = -1 + separation / 2
    coords = [(start_point + (i % dimension) * separation, start_point + (i // dimension) * separation) for i in range(tubule_count)]
    jittered_coords = [(x + random.uniform(-noise, noise), y + random.uniform(-noise, noise)) for x, y in coords]
    for x, y in jittered_coords:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        cylinder = bpy.context.object
        bool_mod = cube_object.modifiers.new(name="BoolMod_{:.2f}_{:.2f}".format(x, y), type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = cylinder
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(cylinder, do_unlink=True)

# Execute structure creation
create_structure(total_tubules, noise_variation)
