# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_script_to_make_geometric_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender script to make geometric pattern.

import bpy
import math

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a material for the circles
material_for_circles = bpy.data.materials.new(name="Material for Circles")
material_for_circles.diffuse_color = (0.2, 0.5, 0.8, 1)  # Soft blue color

# Create interlocking circles using a class
class CircleCreator:
    def __init__(self, count, radius, spacing):
        self.count = count
        self.radius = radius
        self.spacing = spacing

    def generate_circles(self):
        for i in range(self.count):
            self.add_circle(i)

    def add_circle(self, index):
        angle = index * (2 * math.pi / self.count)
        x = self.spacing * math.cos(angle)
        y = self.spacing * math.sin(angle)
        bpy.ops.mesh.primitive_torus_add(location=(x, y, 0), major_radius=self.radius, minor_radius=0.1)
        new_circle = bpy.context.object
        new_circle.name = f"Circle {index + 1}"
        new_circle.data.materials.append(material_for_circles)

# Parameters for the circles
num_of_circles = 5
circle_radius = 1
circle_spacing = 1.5

# Instantiate and generate circles
circle_creator = CircleCreator(num_of_circles, circle_radius, circle_spacing)
circle_creator.generate_circles()


# --- 3DCodeVerse geo variant: neutralize materials (auto-derived, do not edit) ---
import bpy as _bpy_geo
_geo_mat = _bpy_geo.data.materials.get("geo_neutral") or _bpy_geo.data.materials.new("geo_neutral")
try:
    _geo_mat.use_nodes = False
except Exception:
    pass
try:
    _geo_mat.diffuse_color = (0.8, 0.8, 0.8, 1.0)
except Exception:
    pass
for _geo_obj in list(_bpy_geo.data.objects):
    if _geo_obj.type == "MESH" and _geo_obj.data is not None:
        try:
            _geo_obj.data.materials.clear()
            _geo_obj.data.materials.append(_geo_mat)
        except Exception:
            pass
# --- end geo variant ---
