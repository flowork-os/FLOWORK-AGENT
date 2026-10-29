# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_Blender_code_that_constructs_a_model_of_hollow_hexagonal_cell_by_subtrac" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a Blender code that constructs a model of hollow hexagonal cell by subtracting a smaller hexagonal prism from the center of a larger one.

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

# Create the larger hexagonal prism
outer_radius = 1.0
outer_height = 2.0
outer_prism = create_hexagonal_prism("OuterHexPrism", outer_radius, outer_height)

# Create the smaller hexagonal prism
inner_radius = 0.5
inner_height = 2.0
inner_prism = create_hexagonal_prism("InnerHexPrism", inner_radius, inner_height)

# Move the inner prism to the center of the outer prism
inner_prism.location.z = 0  # Center it vertically

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
bpy.data.objects.remove(inner_prism, do_unlink=True)
