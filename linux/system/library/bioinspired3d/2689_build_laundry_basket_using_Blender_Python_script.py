# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_laundry_basket_using_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build laundry basket using Blender Python script

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a rectangular basket

def create_basket(size, location, scale):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    basket_object = bpy.context.object
    basket_object.name = 'Basket'
    basket_object.scale = scale
    return basket_object

# Create the main basket
basket = create_basket(2, (0, 0, 1), (1, 0.7, 0.5))

# Function to create an inner cube for the open top

def create_inner_cube(size, location, scale):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    inner_object = bpy.context.object
    inner_object.name = 'Inner Cube'
    inner_object.scale = scale
    return inner_object

# Create the inner cube
inner_cube = create_inner_cube(2, (0, 0, 1.5), (0.9, 0.65, 0.45))

# Apply boolean modifier to create the open top
bool_modifier = basket.modifiers.new(type='BOOLEAN', name='OpenTopModifier')
bool_modifier.operation = 'DIFFERENCE'
bool_modifier.object = inner_cube
bpy.context.view_layer.objects.active = basket
bpy.ops.object.modifier_apply(modifier='OpenTopModifier')

# Clean up by removing the inner cube
bpy.data.objects.remove(inner_cube, do_unlink=True)
