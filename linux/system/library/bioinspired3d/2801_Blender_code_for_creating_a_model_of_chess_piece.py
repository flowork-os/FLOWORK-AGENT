# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_for_creating_a_model_of_chess_piece" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code for creating a model of chess piece

import bpy

# Remove all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the main structure using different parameters
parts = []

# Create base cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.75, depth=0.2, location=(0, 0, 0.1))
parts.append(bpy.context.object)
parts[-1].name = 'Base'

# Create main body cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=2.8, location=(0, 0, 1.5))
parts.append(bpy.context.object)
parts[-1].name = 'Body'

# Create the top cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=0.2, location=(0, 0, 2.9))
parts.append(bpy.context.object)
parts[-1].name = 'Top'

# Create crown using a cone
bpy.ops.mesh.primitive_cone_add(radius1=0.3, radius2=0.1, depth=0.5, location=(0, 0, 3.25))
parts.append(bpy.context.object)
parts[-1].name = 'Crown'

# Generate torus details
for position in [1.0, 2.0]:
    bpy.ops.mesh.primitive_torus_add(major_radius=0.55, minor_radius=0.05, location=(0, 0, position))
    parts.append(bpy.context.object)
    parts[-1].name = f'Detail{position}'

# Select and join all parts into a single object
bpy.ops.object.select_all(action='DESELECT')
for part in parts:
    part.select_set(True)

bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()

# Scale the combined object to the desired height
bpy.context.object.scale = (1, 1, 3.75 / bpy.context.object.dimensions.z)
bpy.ops.object.transform_apply(scale=True)
