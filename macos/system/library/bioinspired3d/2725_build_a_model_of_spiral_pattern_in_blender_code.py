# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_spiral_pattern_in_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of spiral pattern in blender code

import bpy
import math

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

class SpiralCreator:
    def __init__(self, turns, points_per_turn, radius, height):
        self.turns = turns
        self.points_per_turn = points_per_turn
        self.radius = radius
        self.height = height

    def generate_spiral(self):
        for i in range(self.turns * self.points_per_turn):
            angle = i * (2 * math.pi / self.points_per_turn)
            x = self.radius * angle * math.cos(angle)
            y = self.radius * angle * math.sin(angle)
            z = self.height * (i / self.points_per_turn)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(x, y, z))

# Initialize and create the spiral
spiral = SpiralCreator(turns=5, points_per_turn=50, radius=0.1, height=0.1)
spiral.generate_spiral()
