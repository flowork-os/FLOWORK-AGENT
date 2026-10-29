# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_that_builds_a_model_of_laundry_basket" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code that builds a model of laundry basket.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
basket_container = bpy.context.object
basket_container.name = 'BasketContainer'
basket_container.scale = (1, 0.7, 0.5)

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1.5))
inner_cube_subtract = bpy.context.object
inner_cube_subtract.name = 'InnerCubeSubtract'
inner_cube_subtract.scale = (0.9, 0.65, 0.45)

boolean_mod = basket_container.modifiers.new(type='BOOLEAN', name='SubtractInnerCube')
boolean_mod.operation = 'DIFFERENCE'
boolean_mod.object = inner_cube_subtract
bpy.context.view_layer.objects.active = basket_container
bpy.ops.object.modifier_apply(modifier='SubtractInnerCube')

bpy.data.objects.remove(inner_cube_subtract, do_unlink=True)
