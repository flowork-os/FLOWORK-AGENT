# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_table_lamp_in_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of table lamp in Blender Python script

import bpy

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a function to generate a cylinder
def generate_cylinder(radius, depth, position, label):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = label
    return obj

# Build the lamp structure
base_part = generate_cylinder(0.5, 0.1, (0, 0, 0.05), "BasePart")
stand_part = generate_cylinder(0.05, 1, (0, 0, 0.6), "StandPart")
shade_part = generate_cylinder(0.4, 0.6, (0, 0, 1.3), "ShadePart")

# Create holes on both ends of the shade
for z in (1.6, 1.0):
    hole = generate_cylinder(0.3, 0.01, (0, 0, z), "Hole")
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='ONLY_FACE')
    bpy.ops.object.mode_set(mode='OBJECT')

# Select the shade and join it with the holes
bpy.ops.object.select_all(action='DESELECT')
shade_part.select_set(True)
bpy.ops.object.join()
