# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_generates_a_model_of_decorative_mandala" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that generates a model of decorative mandala

import bpy
import math

# Clear the scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to generate a circular base

def generate_base(radius, position):
    bpy.ops.mesh.primitive_circle_add(radius=radius, location=position)
    return bpy.context.object

# Generate the base
base_model = generate_base(2, (0, 0, 0))
base_model.name = 'Base Circle'

# Function to create various pattern layers

def create_layer(shape_type, count, radius_factor, angle_increment, z_offset=0):
    for i in range(count):
        angle = math.radians(i * angle_increment)
        x = radius_factor * math.cos(angle)
        y = radius_factor * math.sin(angle)
        if shape_type == 'cube':
            bpy.ops.mesh.primitive_cube_add(size=0.3, location=(x, y, z_offset))
            obj = bpy.context.object
            obj.name = f'Cube Layer {i + 1}'
            obj.rotation_euler[2] = angle
        elif shape_type == 'sphere':
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(x, y, z_offset))
            obj = bpy.context.object
            obj.name = f'Sphere Layer {i + 1}'
        elif shape_type == 'cone':
            bpy.ops.mesh.primitive_cone_add(radius1=0.1, depth=0.3, location=(x, y, z_offset))
            obj = bpy.context.object
            obj.name = f'Cone Layer {i + 1}'
            obj.rotation_euler[2] = angle

# Create the different layers of patterns
create_layer('cube', 8, 1.5, 45)
create_layer('sphere', 16, 2, 22.5)
create_layer('cone', 32, 2.5, 11.25)
