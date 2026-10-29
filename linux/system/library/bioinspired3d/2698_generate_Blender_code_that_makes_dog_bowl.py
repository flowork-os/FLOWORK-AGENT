# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_that_makes_dog_bowl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code that makes dog bowl.

import bpy

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

# Create the outer bowl
outer_bowl = create_cylinder(1.5, 0.5, (0, 0, 0), 'OuterBowl')

# Create the inner bowl
inner_bowl = create_cylinder(1.2, 0.4, (0, 0, 0.05), 'InnerBowl')

# Add a boolean modifier to subtract the inner bowl from the outer bowl
bool_mod = outer_bowl.modifiers.new(name='SubtractInner', type='BOOLEAN')
bool_mod.operation = 'DIFFERENCE'
bool_mod.object = inner_bowl
bpy.context.view_layer.objects.active = outer_bowl
bpy.ops.object.modifier_apply(modifier='SubtractInner')

# Delete the inner bowl object
bpy.data.objects.remove(inner_bowl, do_unlink=True)
