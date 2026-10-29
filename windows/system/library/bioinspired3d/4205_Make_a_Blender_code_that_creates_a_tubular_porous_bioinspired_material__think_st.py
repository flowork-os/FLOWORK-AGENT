# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_Blender_code_that_creates_a_tubular_porous_bioinspired_material__think_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a Blender code that creates a tubular porous bioinspired material. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
count_tubules = 25  # Total number of tubules
stretch_amount = 1.8  # Factor to stretch tubules into ellipses
base_radius = 0.05  # Base radius of the tubules

# Create a cube and arrange tubules in a grid
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube_obj = bpy.context.object

# Calculate grid size and spacing
grid_dim = math.ceil(math.sqrt(count_tubules))
spacing = 2 / grid_dim
start_offset = -1 + spacing / 2

# Generate and subtract tubules
for i in range(count_tubules):
    x_pos = start_offset + (i % grid_dim) * spacing
    y_pos = start_offset + (i // grid_dim) * spacing
    bpy.ops.mesh.primitive_cylinder_add(radius=base_radius, depth=3, location=(x_pos, y_pos, 0))
    tubule_obj = bpy.context.object
    tubule_obj.scale[0] *= stretch_amount

    boolean_mod = cube_obj.modifiers.new(name=f"Boolean_{x_pos}_{y_pos}", type='BOOLEAN')
    boolean_mod.operation = 'DIFFERENCE'
    boolean_mod.object = tubule_obj

    bpy.context.view_layer.objects.active = cube_obj
    bpy.ops.object.modifier_apply(modifier=boolean_mod.name)
    bpy.data.objects.remove(tubule_obj, do_unlink=True)
