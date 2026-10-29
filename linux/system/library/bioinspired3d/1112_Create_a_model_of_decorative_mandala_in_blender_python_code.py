# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_decorative_mandala_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of decorative mandala in blender python code

import bpy
import math

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Class to manage pattern creation
class PatternCreator:
    def __init__(self):
        self.base_radius = 2
        self.base_location = (0, 0, 0)

    def create_base(self):
        bpy.ops.mesh.primitive_circle_add(radius=self.base_radius, location=self.base_location)
        return bpy.context.object

    def create_patterns(self):
        self.create_first_layer()
        self.create_second_layer()
        self.create_third_layer()

    def create_first_layer(self):
        for i in range(8):
            angle = math.radians(i * 45)
            x = 1.5 * math.cos(angle)
            y = 1.5 * math.sin(angle)
            bpy.ops.mesh.primitive_cube_add(size=0.3, location=(x, y, 0))
            pattern = bpy.context.object
            pattern.name = f'Layer 1 - Cube {i + 1}'
            pattern.rotation_euler[2] = angle

    def create_second_layer(self):
        for i in range(16):
            angle = math.radians(i * 22.5)
            x = 2 * math.cos(angle)
            y = 2 * math.sin(angle)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(x, y, 0))
            pattern = bpy.context.object
            pattern.name = f'Layer 2 - Sphere {i + 1}'

    def create_third_layer(self):
        for i in range(32):
            angle = math.radians(i * 11.25)
            x = 2.5 * math.cos(angle)
            y = 2.5 * math.sin(angle)
            bpy.ops.mesh.primitive_cone_add(radius1=0.1, depth=0.3, location=(x, y, 0))
            pattern = bpy.context.object
            pattern.name = f'Layer 3 - Cone {i + 1}'
            pattern.rotation_euler[2] = angle

# Execute the creation process
creator = PatternCreator()
creator.create_base()
creator.create_patterns()
