# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_blender_code__create_subway_map" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a blender code, create subway map

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

color_scheme = {
    "Route 1": (1, 0, 0, 1),  # Red
    "Route 2": (0, 1, 0, 1),  # Green
    "Route 3": (0, 0, 1, 1),  # Blue
    "Route 4": (1, 1, 0, 1),  # Yellow
}

def make_line(route_name, route_color, route_points):
    mat = bpy.data.materials.new(name=route_name)
    mat.diffuse_color = route_color
    
    curve = bpy.data.curves.new(name=route_name, type='CURVE')
    curve.dimensions = '3D'
    spline = curve.splines.new('POLY')
    spline.points.add(len(route_points) - 1)
    
    for index, pt in enumerate(route_points):
        spline.points[index].co = (pt[0], pt[1], pt[2], 1)
    
    curve_obj = bpy.data.objects.new(route_name, curve)
    bpy.context.collection.objects.link(curve_obj)
    curve_obj.data.materials.append(mat)
    curve_obj.data.bevel_depth = 0.05

def place_station(coords):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=coords)
    station_mesh = bpy.context.object
    station_mesh.name = "Station"
    station_mesh.data.materials.append(bpy.data.materials.new(name="Station Material"))
    station_mesh.data.materials[0].diffuse_color = (1, 1, 1, 1)  # White

subway_routes = {
    "Route 1": [(0, 0, 0), (1, 2, 0), (2, 3, 0), (3, 5, 0)],
    "Route 2": [(0, 0, 0), (-1, -2, 0), (-2, -3, 0), (-3, -5, 0)],
    "Route 3": [(0, 0, 0), (2, -1, 0), (3, -2, 0), (5, -3, 0)],
    "Route 4": [(0, 0, 0), (-2, 1, 0), (-3, 2, 0), (-5, 3, 0)],
}

for route, points in subway_routes.items():
    make_line(route, color_scheme[route], points)
    for pt in points:
        place_station(pt)


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
