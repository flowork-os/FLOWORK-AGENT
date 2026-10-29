# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_script_that_makes_dog_bowl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender script that makes dog bowl

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to add a bowl with a specific radius and depth

def add_bowl(radius, depth, position, bowl_name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = bowl_name
    return obj

# Create the outer and inner bowls
outer_bowl = add_bowl(1.5, 0.5, (0, 0, 0), 'Bowl_Outer')
inner_bowl = add_bowl(1.2, 0.4, (0, 0, 0.05), 'Bowl_Inner')

# Use a boolean modifier to carve the inner bowl out of the outer bowl
outer_bowl_mod = outer_bowl.modifiers.new(name='CarveLip', type='BOOLEAN')
outer_bowl_mod.operation = 'DIFFERENCE'
outer_bowl_mod.object = inner_bowl
bpy.context.view_layer.objects.active = outer_bowl
bpy.ops.object.modifier_apply(modifier='CarveLip')

# Clean up by removing the inner bowl
bpy.data.objects.remove(inner_bowl, do_unlink=True)
