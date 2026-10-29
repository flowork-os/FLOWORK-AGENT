# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_python_code__construct_a_model_of_mandala_design" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender python code, construct a model of mandala design.

import bpy
import math

# Function to remove all mesh objects

def remove_mesh_objects():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

# Function to add shapes in a circular pattern

def add_shapes_in_circle(radius, total_shapes, shape_style, height=0.1):
    angle_increment = 2 * math.pi / total_shapes
    for index in range(total_shapes):
        angle = index * angle_increment
        x_pos = radius * math.cos(angle)
        y_pos = radius * math.sin(angle)
        
        if shape_style == 'triangle':
            bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.1, depth=height, location=(x_pos, y_pos, 0))
        elif shape_style == 'square':
            bpy.ops.mesh.primitive_cube_add(size=0.2, location=(x_pos, y_pos, 0))
        elif shape_style == 'circle':
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=height, location=(x_pos, y_pos, 0))

# Clear previous objects
remove_mesh_objects()

# Create shapes in concentric circles
add_shapes_in_circle(1, 8, 'triangle')
add_shapes_in_circle(2, 16, 'square')
add_shapes_in_circle(3, 24, 'circle')
add_shapes_in_circle(4, 32, 'triangle')
add_shapes_in_circle(5, 40, 'square')

# Add a central sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 0))
central_shape = bpy.context.object
central_shape.name = 'Core'
