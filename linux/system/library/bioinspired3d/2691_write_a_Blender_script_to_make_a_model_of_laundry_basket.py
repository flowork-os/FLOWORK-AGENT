# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_script_to_make_a_model_of_laundry_basket" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender script to make a model of laundry basket

import bpy

# Clear existing meshes in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a function to create a cube with specific parameters

def add_cube(size, position, scaling):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    cube = bpy.context.object
    cube.scale = scaling
    return cube

# Create the outer basket object
basket = add_cube(2, (0, 0, 1), (1, 0.7, 0.5))

# Create the inner cube for the boolean operation
inner_cube = add_cube(2, (0, 0, 1.5), (0.9, 0.65, 0.45))

# Apply boolean modifier to create the open top
bool_modifier = basket.modifiers.new(type='BOOLEAN', name='CutoutModifier')
bool_modifier.operation = 'DIFFERENCE'
bool_modifier.object = inner_cube
bpy.context.view_layer.objects.active = basket
bpy.ops.object.modifier_apply(modifier='CutoutModifier')

# Remove the inner cube after the boolean operation
bpy.data.objects.remove(inner_cube, do_unlink=True)
