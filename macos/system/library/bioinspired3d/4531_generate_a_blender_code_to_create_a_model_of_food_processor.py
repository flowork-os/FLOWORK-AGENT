# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_blender_code_to_create_a_model_of_food_processor" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a blender code to create a model of food processor

import bpy

# Clear all mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

class ModelBuilder:
    def __init__(self):
        self.objects = []

    def add_cube(self, size, position, name):
        bpy.ops.mesh.primitive_cube_add(size=size, location=position)
        obj = bpy.context.object
        obj.name = name
        self.objects.append(obj)

    def add_plane(self, size, position, name):
        bpy.ops.mesh.primitive_plane_add(size=size, location=position)
        obj = bpy.context.object
        obj.name = name
        self.objects.append(obj)

    def add_cylinder(self, radius, depth, position, name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
        obj = bpy.context.object
        obj.name = name
        self.objects.append(obj)

# Instantiate the model builder
builder = ModelBuilder()

# Create the base
builder.add_cube(2, (0, 0, -1), 'Base')

# Create the control panel
builder.add_plane(0.5, (0, 1.01, -0.75), 'Control Panel')

# Create the bowl
builder.add_cylinder(0.7, 1.2, (0, 0, 0.6), 'Bowl')

# Create the lid
builder.add_cylinder(0.75, 0.1, (0, 0, 1.3), 'Lid')

# Create the feeding tube
builder.add_cylinder(0.2, 0.6, (0, 0.6, 1.5), 'Feeding Tube')
