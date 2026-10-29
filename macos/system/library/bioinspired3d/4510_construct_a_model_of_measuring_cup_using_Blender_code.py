# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_measuring_cup_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of measuring cup using Blender code

import bpy

# Clear the existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cylinder
def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj

# Step 1: Create the outer cup
outer_cup = create_cylinder(1, 2, (0, 0, 1), 'Outer Cup')

# Step 2: Create the inner cup to hollow out the outer cup
inner_cup = create_cylinder(0.9, 2, (0, 0, 1), 'Inner Cup')

# Step 3: Apply boolean modifier to create hollow effect
bool_modifier = outer_cup.modifiers.new(type='BOOLEAN', name='Hollowing Modifier')
bool_modifier.operation = 'DIFFERENCE'
bool_modifier.object = inner_cup
bpy.context.view_layer.objects.active = outer_cup
bpy.ops.object.modifier_apply(modifier='Hollowing Modifier')
bpy.data.objects.remove(inner_cup, do_unlink=True)

# Step 4: Adding measurement markings
for index in range(1, 5):
    bpy.ops.mesh.primitive_plane_add(size=0.1, location=(1.1, 0, index * 0.4))
    marking_plane = bpy.context.object
    marking_plane.name = f'Marking {index}'
    marking_plane.rotation_euler[1] = 1.5708  # Align marking with cup
    
    # Boolean modifier to cut the marking into the outer cup
    marking_bool = outer_cup.modifiers.new(type='BOOLEAN', name=f'Marking Modifier {index}')
    marking_bool.operation = 'DIFFERENCE'
    marking_bool.object = marking_plane
    bpy.context.view_layer.objects.active = outer_cup
    bpy.ops.object.modifier_apply(modifier=f'Marking Modifier {index}')
    bpy.data.objects.remove(marking_plane, do_unlink=True)
