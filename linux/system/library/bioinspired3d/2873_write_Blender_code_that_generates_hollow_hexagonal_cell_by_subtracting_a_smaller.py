# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_Blender_code_that_generates_hollow_hexagonal_cell_by_subtracting_a_smaller" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write Blender code that generates hollow hexagonal cell by subtracting a smaller hexagonal prism from the center of a larger one

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Function to create a hexagonal prism
def create_hexagonal_prism(name, radius, height):
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=radius, depth=height)
    hex_prism = bpy.context.object
    hex_prism.name = name
    return hex_prism

# Create the larger hexagonal prism
outer_radius = 2
outer_height = 3
outer_prism = create_hexagonal_prism("OuterHexPrism", outer_radius, outer_height)

# Create the smaller hexagonal prism
inner_radius = 1.5
inner_height = outer_height + 0.1  # Slightly taller to ensure subtraction
inner_prism = create_hexagonal_prism("InnerHexPrism", inner_radius, inner_height)

# Select both objects for boolean operation
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

# Delete the inner prism as it's no longer needed
bpy.data.objects.remove(inner_prism, do_unlink=True)
