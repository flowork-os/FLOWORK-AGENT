# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_to_build_a_model_of_mri_machine" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender to build a model of mri machine

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cylinder
def create_cylinder(radius, depth, position, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = name
    return obj

# Create the main structure of the MRI device
main_structure = create_cylinder(1.5, 2, (0, 0, 0), 'Main Structure')

# Create the opening in the structure
opening = create_cylinder(1, 2.2, (0, 0, 0), 'Opening')

# Apply boolean modifier to create the opening effect
bool_modifier = main_structure.modifiers.new(name='Boolean Modifier', type='BOOLEAN')
bool_modifier.operation = 'DIFFERENCE'
bool_modifier.object = opening
bpy.context.view_layer.objects.active = main_structure
bpy.ops.object.modifier_apply(modifier='Boolean Modifier')
bpy.data.objects.remove(opening, do_unlink=True)

# Add the control interface
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1.75, 0, 0.75))
control_interface = bpy.context.object
control_interface.name = 'Control Interface'
