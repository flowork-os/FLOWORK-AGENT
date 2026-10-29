# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_to_create_mri_machine" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script to create mri machine

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the central part of the MRI machine
bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=2, location=(0, 0, 0))
central_part = bpy.context.object
central_part.name = 'Central Part'

# Generate the hollow opening
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2.2, location=(0, 0, 0))
hole = bpy.context.object
hole.name = 'Hollow Opening'

# Use a Boolean modifier to subtract the opening from the central part
boolean_modifier = central_part.modifiers.new(name='Subtract', type='BOOLEAN')
boolean_modifier.operation = 'DIFFERENCE'
boolean_modifier.object = hole
bpy.context.view_layer.objects.active = central_part
bpy.ops.object.modifier_apply(modifier='Subtract')
bpy.data.objects.remove(hole, do_unlink=True)

# Create the operational panel
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1.75, 0, 0.75))
operation_panel = bpy.context.object
operation_panel.name = 'Operational Panel'
