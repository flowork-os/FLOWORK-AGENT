# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_python_code_to_create_a_model_of_mandala_design" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender python code to create a model of mandala design

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def generate_circular_pattern(radius, count, shape_type, height=0.1):
    angle_increment = 2 * math.pi / count
    for i in range(count):
        angle = i * angle_increment
        x_position = radius * math.cos(angle)
        y_position = radius * math.sin(angle)
        
        if shape_type == 'triangle':
            bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.1, depth=height, location=(x_position, y_position, 0))
        elif shape_type == 'square':
            bpy.ops.mesh.primitive_cube_add(size=0.2, location=(x_position, y_position, 0))
        elif shape_type == 'circle':
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=height, location=(x_position, y_position, 0))
        
        shape_object = bpy.context.object
        shape_object.rotation_euler[2] = angle

generate_circular_pattern(1, 8, 'triangle')
generate_circular_pattern(2, 16, 'square')
generate_circular_pattern(3, 24, 'circle')
generate_circular_pattern(4, 32, 'triangle')
generate_circular_pattern(5, 40, 'square')

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 0))
central_sphere = bpy.context.object
central_sphere.name = 'Central Sphere'
