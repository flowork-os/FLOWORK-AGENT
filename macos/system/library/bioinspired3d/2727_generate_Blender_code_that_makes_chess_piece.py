# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_that_makes_chess_piece" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code that makes chess piece

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cylinder

def create_cylinder(radius, depth, position, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = name
    return obj

# Generate the base component
base_part = create_cylinder(0.75, 0.2, (0, 0, 0.1), 'Base')

# Generate the main body
body_part = create_cylinder(0.5, 2.8, (0, 0, 1.5), 'Body')

# Generate the top section
top_part = create_cylinder(0.6, 0.2, (0, 0, 2.9), 'Top')

# Create the crown using a cone
bpy.ops.mesh.primitive_cone_add(radius1=0.3, radius2=0.1, depth=0.5, location=(0, 0, 3.25))
crown_part = bpy.context.object
crown_part.name = 'Crown'

# Function to create a torus detail

def create_torus(major_radius, minor_radius, position, name):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_radius, minor_radius=minor_radius, location=position)
    obj = bpy.context.object
    obj.name = name
    return obj

# Add intricate details
first_detail = create_torus(0.55, 0.05, (0, 0, 1.0), 'Detail1')
second_detail = create_torus(0.55, 0.05, (0, 0, 2.0), 'Detail2')

# Select all parts for joining
bpy.ops.object.select_all(action='DESELECT')
for obj in [base_part, body_part, top_part, crown_part, first_detail, second_detail]:
    obj.select_set(True)

# Join all selected objects into one
bpy.context.view_layer.objects.active = base_part
bpy.ops.object.join()

# Adjust the scale of the final object
bpy.context.object.scale = (1, 1, 3.75 / bpy.context.object.dimensions.z)
bpy.ops.object.transform_apply(scale=True)
