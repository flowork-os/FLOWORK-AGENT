# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_python_code_to_create_a_model_of_subway_map" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender python code to create a model of subway map

import bpy

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define colors for the subway lines
line_colors = {
    "Red Line": (1, 0, 0, 1),  # Red
    "Green Line": (0, 1, 0, 1),  # Green
    "Blue Line": (0, 0, 1, 1),  # Blue
    "Yellow Line": (1, 1, 0, 1),  # Yellow
}

# Helper function to generate a subway line
def generate_line(line_name, line_color, coordinates):
    line_material = bpy.data.materials.new(name=line_name)
    line_material.diffuse_color = line_color
    
    # Create a new curve object
    curve_data = bpy.data.curves.new(name=line_name, type='CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(coordinates) - 1)
    
    for index, coord in enumerate(coordinates):
        spline.points[index].co = (coord[0], coord[1], coord[2], 1)
    
    curve_object = bpy.data.objects.new(line_name, curve_data)
    bpy.context.collection.objects.link(curve_object)
    curve_object.data.materials.append(line_material)
    
    # Set the bevel for the curve to create a tube effect
    curve_object.data.bevel_depth = 0.05

# Function to create a station at a given location
def add_station(position):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=position)
    station_object = bpy.context.object
    station_object.name = "Subway Station"
    station_object.data.materials.append(bpy.data.materials.new(name="Station Material"))
    station_object.data.materials[0].diffuse_color = (1, 1, 1, 1)  # White

# Define subway lines with their respective coordinates
subway_routes = {
    "Red Line": [(0, 0, 0), (1, 2, 0), (2, 3, 0), (3, 5, 0)],
    "Green Line": [(0, 0, 0), (-1, -2, 0), (-2, -3, 0), (-3, -5, 0)],
    "Blue Line": [(0, 0, 0), (2, -1, 0), (3, -2, 0), (5, -3, 0)],
    "Yellow Line": [(0, 0, 0), (-2, 1, 0), (-3, 2, 0), (-5, 3, 0)],
}

# Create the subway lines and stations
for route_name, coords in subway_routes.items():
    generate_line(route_name, line_colors[route_name], coords)
    for coord in coords:
        add_station(coord)


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
