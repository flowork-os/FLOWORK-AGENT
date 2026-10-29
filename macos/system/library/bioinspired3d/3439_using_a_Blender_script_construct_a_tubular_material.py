# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_script_construct_a_tubular_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender script construct a tubular material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define parameters for the structure
num_tubules = 12  # Total number of tubules
ellipse_scale = 1.8  # Factor to stretch tubules into ellipses
tubule_diameter = 0.06  # Base radius of the tubules

# Function to generate the tubule structure

def generate_tubule_cube(count, stretch, radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    grid_dim = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2

    for i in range(count):
        x = offset + (i % grid_dim) * spacing
        y = offset + (i // grid_dim) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule_instance = bpy.context.object
        tubule_instance.scale[0] *= stretch

        bool_modifier = cube_object.modifiers.new(name=f"Boolean_{i}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule_instance

        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule_instance, do_unlink=True)

generate_tubule_cube(num_tubules, ellipse_scale, tubule_diameter)
