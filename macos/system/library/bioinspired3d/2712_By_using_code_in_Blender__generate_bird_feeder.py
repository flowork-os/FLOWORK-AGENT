# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_code_in_Blender__generate_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using code in Blender, generate bird feeder

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cylinder

def create_cylinder(radius, depth, location, rotation=(0, 0, 0), name='Cylinder'):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return obj

# Create the main cylindrical body
body_cylinder = create_cylinder(0.5, 1.0, (0, 0, 0.5), name='MainBody')

# Create the conical roof
bpy.ops.mesh.primitive_cone_add(radius1=0.6, depth=0.3, location=(0, 0, 1.15))
roof_cone = bpy.context.object
roof_cone.name = 'RoofCone'

# Create a perch using a cylinder
perch_cylinder = create_cylinder(0.05, 0.4, (0.55, 0, 0.3), rotation=(0, math.pi/2, 0), name='PerchCylinder')

# Create an opening using a smaller cylinder
opening_cylinder = create_cylinder(0.15, 0.1, (0.5, 0, 0.6), name='OpeningCylinder')

# Apply a Boolean modifier to create an opening in the body
bool_modifier = body_cylinder.modifiers.new(name='BooleanModifier', type='BOOLEAN')
bool_modifier.operation = 'DIFFERENCE'
bool_modifier.object = opening_cylinder
bpy.context.view_layer.objects.active = body_cylinder
bpy.ops.object.modifier_apply(modifier='BooleanModifier')

# Remove the opening object after applying the modifier
bpy.data.objects.remove(opening_cylinder, do_unlink=True)
