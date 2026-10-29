# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_Python_script_that_creates_measuring_cup" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender Python script that creates measuring cup

import bpy

# Deselect and delete all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create and hollow out the measuring cup
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 1))
measuring_cup = bpy.context.object
measuring_cup.name = 'Cup'

bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=2, location=(0, 0, 1))
inner_cup = bpy.context.object
inner_cup.name = 'Inner Cup'

# Use a boolean modifier to hollow out the cup
bool_mod = measuring_cup.modifiers.new(type='BOOLEAN', name='Hollowing')
bool_mod.operation = 'DIFFERENCE'
bool_mod.object = inner_cup
bpy.context.view_layer.objects.active = measuring_cup
bpy.ops.object.modifier_apply(modifier='Hollowing')
bpy.data.objects.remove(inner_cup, do_unlink=True)

# Create measurement markings
for i in range(1, 5):
    bpy.ops.mesh.primitive_plane_add(size=0.1, location=(1, 0, i * 0.4))
    marking = bpy.context.object
    marking.name = f'Marking {i}'
    marking.rotation_euler[1] = 1.5708  # Align marking with cup
    
    # Cut the marking into the cup using a boolean modifier
    marking_bool = measuring_cup.modifiers.new(type='BOOLEAN', name=f'Marking Cut {i}')
    marking_bool.operation = 'DIFFERENCE'
    marking_bool.object = marking
    bpy.context.view_layer.objects.active = measuring_cup
    bpy.ops.object.modifier_apply(modifier=f'Marking Cut {i}')
    bpy.data.objects.remove(marking, do_unlink=True)
