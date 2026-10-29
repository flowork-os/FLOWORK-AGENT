# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_code_in_Blender_make_a_model_of_hat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using code in Blender make a model of hat

import bpy

# Start by clearing the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a method for cylinder creation
def create_mesh_cylinder(radius, depth, position, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    mesh = bpy.context.object
    mesh.name = name
    return mesh

# Create the components of the model
brim_shape = create_mesh_cylinder(1.5, 0.1, (0, 0, 0), 'Brim')
crown_shape = create_mesh_cylinder(0.75, 1, (0, 0, 0.55), 'Crown')
