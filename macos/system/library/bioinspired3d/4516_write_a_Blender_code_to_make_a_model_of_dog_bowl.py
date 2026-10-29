# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_to_make_a_model_of_dog_bowl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code to make a model of dog bowl.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cylinder
def create_cylinder(radius, depth, z_location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=(0, 0, z_location))
    obj = bpy.context.object
    obj.name = name
    return obj

# Create the base of the bowl
base = create_cylinder(1.5, 0.5, 0, 'Bowl Base')
# Create the inner part of the bowl
inner_part = create_cylinder(1.3, 0.4, 0.05, 'Bowl Inner')

# Apply a boolean modifier to hollow out the bowl
bool_modifier = base.modifiers.new(type='BOOLEAN', name='Hollowing')
bool_modifier.object = inner_part
bool_modifier.operation = 'DIFFERENCE'
bpy.context.view_layer.objects.active = base
bpy.ops.object.modifier_apply(modifier='Hollowing')

# Remove the inner cylinder
bpy.data.objects.remove(inner_part, do_unlink=True)

# Create the raised edge of the bowl
raised_edge = bpy.ops.mesh.primitive_torus_add(major_radius=1.5, minor_radius=0.1, location=(0, 0, 0.25))
raised_edge = bpy.context.object
raised_edge.name = 'Raised Edge'

# Combine the base and the raised edge into one object
bpy.ops.object.select_all(action='DESELECT')
base.select_set(True)
raised_edge.select_set(True)
bpy.context.view_layer.objects.active = base
bpy.ops.object.join()
