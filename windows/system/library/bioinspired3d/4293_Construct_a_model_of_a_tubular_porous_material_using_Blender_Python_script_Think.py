# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_a_tubular_porous_material_using_Blender_Python_script_Think" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of a tubular porous material using Blender Python script Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular grid
total_tubules = 25  # Number of tubules
ellipse_factor = 1.2  # Ellipticity of the tubules
radius_of_tubule = 0.05  # Radius of each tubule

def create_tubular_grid(total_tubules, ellipse_factor=1.0, radius_of_tubule=0.1):
    # Create a cube and subtract tubules from it
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    grid_dim = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_dim
    start_position = -1 + spacing / 2
    for i in range(total_tubules):
        x = start_position + (i % grid_dim) * spacing
        y = start_position + (i // grid_dim) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=radius_of_tubule, depth=3, location=(x, y, 0))
        current_tubule = bpy.context.object
        current_tubule.scale[0] *= ellipse_factor
        mod = cube_base.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = current_tubule
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(current_tubule, do_unlink=True)

create_tubular_grid(total_tubules, ellipse_factor, radius_of_tubule)
