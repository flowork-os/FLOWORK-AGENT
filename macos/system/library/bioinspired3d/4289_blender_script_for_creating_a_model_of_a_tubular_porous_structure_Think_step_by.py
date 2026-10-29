# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_creating_a_model_of_a_tubular_porous_structure_Think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for creating a model of a tubular porous structure Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure settings
num_tubules = 25
ellipticity_value = 1.2
radius_tubule = 0.05

def generate_tubule_positions(count):
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    return [(start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing) for i in range(count)]

def create_structure():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    positions = generate_tubule_positions(num_tubules)

    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius_tubule, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity_value

        bool_modifier = cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule

        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Run the structure creation
create_structure()
