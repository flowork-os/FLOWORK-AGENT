# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_script_create_a_model_of_a_tubular_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender script create a model of a tubular bioinspired structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular model
num_tubules = 25  # Total number of tubules
ellipse_factor = 2.0  # Factor to stretch tubules into ellipses
radius_of_tubules = 0.05  # Base radius of the tubules

# Function to create a cube with a grid of tubules

def make_tubule_structure(tubule_count, ellipticity, radius):
    cube = bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    for i in range(tubule_count):
        x = offset + (i % grid_size) * spacing
        y = offset + (i // grid_size) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity

        modifier = main_cube.modifiers.new(name=f"Boolean_{i}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule

        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

make_tubule_structure(num_tubules, ellipse_factor, radius_of_tubules)
