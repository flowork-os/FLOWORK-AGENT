# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_script__create_a_model_of_a_tubular_material_think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender script, create a model of a tubular material think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
num_tubules = 12
ellipticity_factor = 1.8
radius_value = 0.1

def create_tubular_structure(num_tubules, ellipticity_factor, radius_value):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2

    for i in range(num_tubules):
        x = start_offset + (i % grid_size) * spacing
        y = start_offset + (i // grid_size) * spacing
        add_tubule(cube, x, y, radius_value, ellipticity_factor)

def add_tubule(cube, x, y, radius, ellipticity):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
    tubule = bpy.context.object
    tubule.scale[0] *= ellipticity

    modifier = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
    modifier.operation = 'DIFFERENCE'
    modifier.object = tubule

    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(tubule, do_unlink=True)

create_tubular_structure(num_tubules, ellipticity_factor, radius_value)
