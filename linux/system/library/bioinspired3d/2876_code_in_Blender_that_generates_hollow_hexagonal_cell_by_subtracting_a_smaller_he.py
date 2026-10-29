# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_that_generates_hollow_hexagonal_cell_by_subtracting_a_smaller_he" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender that generates hollow hexagonal cell by subtracting a smaller hexagonal prism from the center of a larger one.

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
create_hexagonal_prism("OuterHexagon", outer_radius, outer_height)

# Create the smaller hexagonal prism
inner_radius = 0.5
inner_height = outer_height + 0.1  # Slightly taller to ensure subtraction
create_hexagonal_prism("InnerHexagon", inner_radius, inner_height)

# Select both objects for boolean operation
bpy.ops.object.select_all(action='DESELECT')
bpy.data.objects["OuterHexagon"].select_set(True)
bpy.data.objects["InnerHexagon"].select_set(True)

# Set the active object to the outer hexagon
bpy.context.view_layer.objects.active = bpy.data.objects["OuterHexagon"]

# Perform the boolean difference operation
bpy.ops.object.modifier_add(type='BOOLEAN')
bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["InnerHexagon"]
bpy.ops.object.modifier_apply(modifier="Boolean")

# Delete the inner hexagon object
bpy.data.objects.remove(bpy.data.objects["InnerHexagon"], do_unlink=True)
