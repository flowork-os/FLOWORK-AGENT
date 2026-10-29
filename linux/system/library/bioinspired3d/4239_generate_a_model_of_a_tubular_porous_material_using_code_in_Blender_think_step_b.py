# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_a_tubular_porous_material_using_code_in_Blender_think_step_b" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of a tubular porous material using code in Blender think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tubule_count = 20
ellipticity_factor = 1.8
base_radius = 0.1

def add_tubule(cube, position, radius, ellipticity):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=position)
    tubule = bpy.context.object
    tubule.scale[0] *= ellipticity
    
    bool_modifier = cube.modifiers.new(name="Tubule_Boolean", type='BOOLEAN')
    bool_modifier.operation = 'DIFFERENCE'
    bool_modifier.object = tubule
    
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
    bpy.data.objects.remove(tubule, do_unlink=True)

def construct_tubular_cube(count, ellipticity, radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(count)]
    
    for pos in positions:
        add_tubule(cube, (pos[0], pos[1], 0), radius, ellipticity)

construct_tubular_cube(tubule_count, ellipticity_factor, base_radius)
