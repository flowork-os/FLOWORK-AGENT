# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_a_tubular_porous_bioinspired_material_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of a tubular porous bioinspired material using blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the number of tubular elements
num_elements = 21

def create_cube():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    return bpy.context.object

def arrange_tubes(count):
    dim = math.ceil(math.sqrt(count))
    spacing = 2 / dim
    offset = -1 + spacing / 2
    return [(offset + (i % dim) * spacing,
             offset + (i // dim) * spacing)
            for i in range(count)]

def apply_boolean(cube, positions):
    for (x, y) in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object
        
        bool_mod = cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tube
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tube, do_unlink=True)

# Create the structure
cube = create_cube()
positions = arrange_tubes(num_elements)
apply_boolean(cube, positions)
