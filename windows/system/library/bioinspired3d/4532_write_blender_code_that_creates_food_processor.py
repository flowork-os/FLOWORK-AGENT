# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_code_that_creates_food_processor" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender code that creates food processor

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the base
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, -1))
base_object = bpy.context.object
base_object.name = 'Base'

# Create the control panel
bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, 1.01, -0.75))
control_panel_object = bpy.context.object
control_panel_object.name = 'Control Panel'

# Create the bowl
bpy.ops.mesh.primitive_cylinder_add(radius=0.7, depth=1.2, location=(0, 0, 0.6))
bowl_object = bpy.context.object
bowl_object.name = 'Bowl'

# Create the lid
bpy.ops.mesh.primitive_cylinder_add(radius=0.75, depth=0.1, location=(0, 0, 1.3))
lid_object = bpy.context.object
lid_object.name = 'Lid'

# Create the feeding tube
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.6, location=(0, 0.6, 1.5))
feeding_tube_object = bpy.context.object
feeding_tube_object.name = 'Feeding Tube'
