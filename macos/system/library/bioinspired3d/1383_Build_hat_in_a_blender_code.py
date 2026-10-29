# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_hat_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build hat in a blender code

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a cylinder with specified properties

def add_cylinder_to_scene(radius, height, position, obj_name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    cylinder = bpy.context.object
    cylinder.name = obj_name

# Generate the brim and crown of the object
add_cylinder_to_scene(1.5, 0.1, (0, 0, 0), 'Brim')
add_cylinder_to_scene(0.75, 1, (0, 0, 0.55), 'Crown')
