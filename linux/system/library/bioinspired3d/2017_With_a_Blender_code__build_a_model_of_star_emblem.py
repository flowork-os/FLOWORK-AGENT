# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_code__build_a_model_of_star_emblem" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender code, build a model of star emblem.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

class Star:
    def __init__(self, points, outer_r, inner_r, offset):
        self.num_points = points
        self.outer_radius = outer_r
        self.inner_radius = inner_r
        self.angle_offset = offset

    def generate_vertices(self):
        vertices = []
        for i in range(self.num_points * 2):
            angle = i * math.pi / self.num_points + self.angle_offset
            radius = self.outer_radius if i % 2 == 0 else self.inner_radius
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            vertices.append((x, y, 0))
        return vertices

star_shape = Star(5, 1, 0.5, math.pi / 2)
star_vertices = star_shape.generate_vertices()

star_mesh = bpy.data.meshes.new('StarGeometry')
star_mesh.from_pydata(star_vertices, [], [(i, (i + 1) % (10), (i + 2) % (10)) for i in range(0, 10, 2)])
star_mesh.update()

star_object = bpy.data.objects.new('StarShape', star_mesh)
bpy.context.collection.objects.link(star_object)
