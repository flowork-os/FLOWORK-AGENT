# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_code__build_a_model_of_coffee_cup" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender code, build a model of coffee cup.

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cylinder

def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj

# Create the main cup
cup_object = create_cylinder(1, 2, (0, 0, 1), 'Cup')

# Create inner cylinder for hollowing
inner_cup_object = create_cylinder(0.9, 1.8, (0, 0, 1.1), 'Inner Cup')

# Apply boolean modifier to hollow the cup
bool_modifier = cup_object.modifiers.new(name='Hollow', type='BOOLEAN')
bool_modifier.operation = 'DIFFERENCE'
bool_modifier.object = inner_cup_object
bpy.context.view_layer.objects.active = cup_object
bpy.ops.object.modifier_apply(modifier='Hollow')
bpy.data.objects.remove(inner_cup_object, do_unlink=True)

# Function to create a handle using a torus

def create_handle(location, major_radius, minor_radius, rotation, name):
    bpy.ops.mesh.primitive_torus_add(align='WORLD', location=location, major_radius=major_radius, minor_radius=minor_radius, rotation=rotation)
    handle_obj = bpy.context.object
    handle_obj.name = name
    return handle_obj

# Create the handle
handle_object = create_handle((1.5, 0, 1.5), 0.5, 0.1, (math.pi / 2, 0, 0), 'Handle')

# Combine the cup and handle
bpy.context.view_layer.objects.active = cup_object
handle_object.select_set(True)
bpy.ops.object.join()
