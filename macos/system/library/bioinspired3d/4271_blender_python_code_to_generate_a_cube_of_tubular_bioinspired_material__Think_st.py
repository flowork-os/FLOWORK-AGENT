# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_to_generate_a_cube_of_tubular_bioinspired_material__Think_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code to generate a cube of tubular bioinspired material. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the structure
count_of_tubules = 9  # Total number of tubules
stretch_factor = 1.1  # Factor to stretch tubules into ellipses
base_radius = 0.08  # Base radius of the tubules

# Function to create tubules within a cube
def create_tubules_in_cube(tubule_count, ellipticity, radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2

    for i in range(tubule_count):
        x_pos = start_offset + (i % grid_size) * spacing
        y_pos = start_offset + (i // grid_size) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x_pos, y_pos, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity

        bool_mod = cube.modifiers.new(name=f"Boolean_{x_pos}_{y_pos}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule

        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

create_tubules_in_cube(count_of_tubules, stretch_factor, base_radius)
