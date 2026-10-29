# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_builds_dog_bowl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that builds dog bowl.

import bpy

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the bowl base using a cylinder
bowl_base = bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=0.5, location=(0, 0, 0))
bowl_base_obj = bpy.context.object
bowl_base_obj.name = 'Bowl Base'

# Add the inner cylinder for hollowing
bowl_inner = bpy.ops.mesh.primitive_cylinder_add(radius=1.3, depth=0.4, location=(0, 0, 0.05))
bowl_inner_obj = bpy.context.object
bowl_inner_obj.name = 'Inner Cylinder'

# Create a boolean modifier to hollow out the bowl
boolean_modifier = bowl_base_obj.modifiers.new(type='BOOLEAN', name='Hollowing Modifier')
boolean_modifier.object = bowl_inner_obj
boolean_modifier.operation = 'DIFFERENCE'
bpy.context.view_layer.objects.active = bowl_base_obj
bpy.ops.object.modifier_apply(modifier='Hollowing Modifier')

# Remove the inner cylinder from the scene
bpy.data.objects.remove(bowl_inner_obj, do_unlink=True)

# Create the raised edge using a torus
bpy.ops.mesh.primitive_torus_add(major_radius=1.5, minor_radius=0.1, location=(0, 0, 0.25))
raised_edge_obj = bpy.context.object
raised_edge_obj.name = 'Raised Edge'

# Join the bowl base and the raised edge into a single object
bpy.ops.object.select_all(action='DESELECT')
bowl_base_obj.select_set(True)
raised_edge_obj.select_set(True)
bpy.context.view_layer.objects.active = bowl_base_obj
bpy.ops.object.join()
