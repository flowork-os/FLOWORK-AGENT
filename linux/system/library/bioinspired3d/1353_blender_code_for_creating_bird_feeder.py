# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_for_creating_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code for creating bird feeder.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a cylindrical object function

def add_cylinder(radius, height, position, identifier):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    new_obj = bpy.context.object
    new_obj.name = identifier
    return new_obj

# Construct the components
main_part = add_cylinder(0.3, 1, (0, 0, 0.5), 'CylinderBody')
foundation_part = add_cylinder(0.35, 0.05, (0, 0, 0.025), 'BasePlate')

# Create the cone for the roof
bpy.ops.mesh.primitive_cone_add(radius1=0.4, depth=0.2, location=(0, 0, 1.1))
roof_part = bpy.context.object
roof_part.name = 'RoofCone'
