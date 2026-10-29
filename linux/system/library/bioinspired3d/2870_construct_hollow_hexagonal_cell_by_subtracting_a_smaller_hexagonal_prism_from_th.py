# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_hollow_hexagonal_cell_by_subtracting_a_smaller_hexagonal_prism_from_th" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct hollow hexagonal cell by subtracting a smaller hexagonal prism from the center of a larger one in Blender Python script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Function to create a hexagonal prism
def create_hexagonal_prism(radius, height):
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=radius, depth=height)
    hex_prism = bpy.context.object
    return hex_prism

# Create the larger hexagonal prism
large_prism = create_hexagonal_prism(radius=2, height=3)

# Create the smaller hexagonal prism
small_prism = create_hexagonal_prism(radius=1.5, height=3)

# Move the smaller prism to the center of the larger prism
small_prism.location.z = 0

# Select both prisms
bpy.ops.object.select_all(action='DESELECT')
large_prism.select_set(True)
small_prism.select_set(True)

# Boolean modifier to subtract the smaller prism from the larger one
bpy.context.view_layer.objects.active = large_prism
bpy.ops.object.modifier_add(type='BOOLEAN')
bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
bpy.context.object.modifiers["Boolean"].object = small_prism

# Apply the modifier
bpy.ops.object.modifier_apply(modifier="Boolean")

# Delete the smaller prism
bpy.data.objects.remove(small_prism)
