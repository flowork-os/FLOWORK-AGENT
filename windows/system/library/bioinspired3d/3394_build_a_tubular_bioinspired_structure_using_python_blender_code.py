# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_tubular_bioinspired_structure_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a tubular bioinspired structure using python blender code

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the parameters
count_tubules = 25
ellipticity_value = 1.8
radius_value = 0.05

def create_structure(count, ellipticity, radius):
    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(count)]

    for pos in positions:
        create_tubule(pos, radius, ellipticity, base_cube)

def create_tubule(position, radius, ellipticity, base_cube):
    x, y = position
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
    tubule = bpy.context.object
    tubule.scale[0] *= ellipticity
    boolean_modifier = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
    boolean_modifier.operation = 'DIFFERENCE'
    boolean_modifier.object = tubule
    bpy.context.view_layer.objects.active = base_cube
    bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
    bpy.data.objects.remove(tubule, do_unlink=True)

create_structure(count_tubules, ellipticity_value, radius_value)
