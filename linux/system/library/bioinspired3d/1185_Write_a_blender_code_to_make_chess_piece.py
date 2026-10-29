# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_blender_code_to_make_chess_piece" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a blender code to make chess piece

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Class to handle the creation of geometric shapes
class ShapeCreator:
    @staticmethod
    def add_cylinder(radius, height, position, identifier):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
        new_obj = bpy.context.object
        new_obj.name = identifier

# Instantiate the shape creator
shape_creator = ShapeCreator()

# Build the model components
shape_creator.add_cylinder(1, 0.2, (0, 0, 0), 'Base')
shape_creator.add_cylinder(0.6, 1.5, (0, 0, 0.85), 'Body')
shape_creator.add_cylinder(0.4, 0.3, (0, 0, 1.85), 'Neck')

# Create the head with a sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 2.3))
head = bpy.context.object
head.name = 'Head'
