# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_subway_map_in_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create subway map in a Blender code

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Color definitions for subway lines
color_map = {
    "Line A": (1, 0, 0, 1),  # Red
    "Line B": (0, 1, 0, 1),  # Green
    "Line C": (0, 0, 1, 1),  # Blue
    "Line D": (1, 1, 0, 1),  # Yellow
}

class SubwaySystem:
    def __init__(self):
        self.routes = {
            "Line A": [(0, 0, 0), (1, 2, 0), (2, 3, 0), (3, 5, 0)],
            "Line B": [(0, 0, 0), (-1, -2, 0), (-2, -3, 0), (-3, -5, 0)],
            "Line C": [(0, 0, 0), (2, -1, 0), (3, -2, 0), (5, -3, 0)],
            "Line D": [(0, 0, 0), (-2, 1, 0), (-3, 2, 0), (-5, 3, 0)],
        }

    def create_line(self, name, color, points):
        material = bpy.data.materials.new(name=name)
        material.diffuse_color = color
        
        curve_data = bpy.data.curves.new(name=name, type='CURVE')
        polyline = curve_data.splines.new('POLY')
        polyline.points.add(len(points) - 1)
        
        for i, point in enumerate(points):
            polyline.points[i].co = (point[0], point[1], point[2], 1)
        
        curve_object = bpy.data.objects.new(name, curve_data)
        bpy.context.collection.objects.link(curve_object)
        curve_object.data.materials.append(material)
        curve_object.data.bevel_depth = 0.05

    def create_station(self, loc):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=loc)
        station = bpy.context.object
        station.name = "Station"
        station.data.materials.append(bpy.data.materials.new(name="Station Material"))
        station.data.materials[0].diffuse_color = (1, 1, 1, 1)  # White

    def build(self):
        for line_name, points in self.routes.items():
            self.create_line(line_name, color_map[line_name], points)
            for point in points:
                self.create_station(point)

# Instantiate and build the subway system
subway = SubwaySystem()
subway.build()


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
