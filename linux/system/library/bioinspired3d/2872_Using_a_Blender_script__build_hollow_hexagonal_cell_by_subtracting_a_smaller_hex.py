# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_Blender_script__build_hollow_hexagonal_cell_by_subtracting_a_smaller_hex" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a Blender script, build hollow hexagonal cell by subtracting a smaller hexagonal prism from the center of a larger one.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Function to create a hexagonal prism
def create_hexagonal_prism(name, radius, height):
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=radius, depth=height)
    obj = bpy.context.active_object
    obj.name = name
    return obj

# Parameters for the hexagonal cells
outer_radius = 1.0
inner_radius = 0.5
height = 2.0

# Create the outer hexagonal prism
outer_prism = create_hexagonal_prism("OuterHexPrism", outer_radius, height)

# Create the inner hexagonal prism
inner_prism = create_hexagonal_prism("InnerHexPrism", inner_radius, height)

# Move the inner prism to the center of the outer prism
inner_prism.location = outer_prism.location

# Select both objects for the boolean operation
bpy.ops.object.select_all(action='DESELECT')
outer_prism.select_set(True)
inner_prism.select_set(True)

# Set the active object to the outer prism
bpy.context.view_layer.objects.active = outer_prism

# Perform the boolean difference operation
bpy.ops.object.modifier_add(type='BOOLEAN')
bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
bpy.context.object.modifiers["Boolean"].object = inner_prism
bpy.ops.object.modifier_apply(modifier="Boolean")

# Delete the inner prism
bpy.data.objects.remove(inner_prism)
