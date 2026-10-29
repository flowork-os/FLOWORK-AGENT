# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_that_constructs_dog_bowl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code that constructs dog bowl

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the main bowl shape
bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=0.2, location=(0, 0, 0))
bowl_shape = bpy.context.object
bowl_shape.name = "Bowl Shape"

# Create the inner part of the bowl
bpy.ops.mesh.primitive_cylinder_add(radius=1.3, depth=0.1, location=(0, 0, 0.1))
inner_part = bpy.context.object
inner_part.name = "Inner Part"

# Use the Boolean modifier to hollow out the bowl
bowl_shape.modifiers.new(name="Hollow", type='BOOLEAN')
bowl_shape.modifiers[0].operation = 'DIFFERENCE'
bowl_shape.modifiers[0].object = inner_part
bpy.context.view_layer.objects.active = bowl_shape
bpy.ops.object.modifier_apply(modifier="Hollow")

# Delete the inner part from the scene
bpy.data.objects.remove(inner_part, do_unlink=True)
