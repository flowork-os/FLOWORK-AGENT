# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_coffee_cup_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build coffee cup in a Blender script

import bpy
import math

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the cup geometry
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 1))
cup_instance = bpy.context.object
cup_instance.name = 'Cup'

# Create an inner cylinder to subtract
bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=1.8, location=(0, 0, 1.1))
inner_cup_instance = bpy.context.object
inner_cup_instance.name = 'Inner Cup'

# Set up and apply the boolean modifier to hollow out the cup
boolean_modifier = cup_instance.modifiers.new(name='Hollow', type='BOOLEAN')
boolean_modifier.operation = 'DIFFERENCE'
boolean_modifier.object = inner_cup_instance
bpy.context.view_layer.objects.active = cup_instance
bpy.ops.object.modifier_apply(modifier='Hollow')
bpy.data.objects.remove(inner_cup_instance, do_unlink=True)

# Create the handle using a torus
bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(1.5, 0, 1.5), major_radius=0.5, minor_radius=0.1, rotation=(math.pi / 2, 0, 0))
handle_instance = bpy.context.object
handle_instance.name = 'Handle'

# Join the cup and handle into one object
bpy.context.view_layer.objects.active = cup_instance
handle_instance.select_set(True)
bpy.ops.object.join()
