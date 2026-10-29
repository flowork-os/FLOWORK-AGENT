# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_python_blender_code_that_creates_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write python blender code that creates bird feeder.

import bpy
import math

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a function to generate the 3D components

def generate_component(component_type, params):
    if component_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(**params)
    elif component_type == 'cone':
        bpy.ops.mesh.primitive_cone_add(**params)

# Parameters for the components
body_params = {'radius': 0.5, 'depth': 1.0, 'location': (0, 0, 0.5)}
roof_params = {'radius1': 0.6, 'depth': 0.3, 'location': (0, 0, 1.15)}
perch_params = {'radius': 0.05, 'depth': 0.4, 'location': (0.55, 0, 0.3), 'rotation': (0, math.pi/2, 0)}
opening_params = {'radius': 0.15, 'depth': 0.1, 'location': (0.5, 0, 0.6)}

# Create the body and roof
generate_component('cylinder', body_params)
body_object = bpy.context.object
body_object.name = 'Body'

generate_component('cone', roof_params)
roof_object = bpy.context.object
roof_object.name = 'Roof'

# Create the perch and opening
generate_component('cylinder', perch_params)
perch_object = bpy.context.object
perch_object.name = 'Perch'

generate_component('cylinder', opening_params)
opening_object = bpy.context.object
opening_object.name = 'Opening'

# Set up the Boolean modifier to cut the opening in the body
bool_modifier = body_object.modifiers.new(name='BooleanCut', type='BOOLEAN')
bool_modifier.operation = 'DIFFERENCE'
bool_modifier.object = opening_object
bpy.context.view_layer.objects.active = body_object
bpy.ops.object.modifier_apply(modifier='BooleanCut')

# Remove the opening object after applying the modifier
bpy.data.objects.remove(opening_object, do_unlink=True)
