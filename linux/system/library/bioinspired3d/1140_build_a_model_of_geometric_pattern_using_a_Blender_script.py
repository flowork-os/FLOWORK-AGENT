# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_geometric_pattern_using_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of geometric pattern using a Blender script

import bpy
import math

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the circles
circle_material = bpy.data.materials.new(name="Circle Material")
circle_material.diffuse_color = (0.7, 0.3, 0.3, 1)  # Light red color

# Function to create a torus at a specific angle

def create_circle(index, radius, offset):
    angle = index * (2 * math.pi / num_circles)
    x = offset * math.cos(angle)
    y = offset * math.sin(angle)
    bpy.ops.mesh.primitive_torus_add(location=(x, y, 0), major_radius=radius, minor_radius=0.1)
    current_circle = bpy.context.object
    current_circle.name = f"Circle {index + 1}"
    current_circle.data.materials.append(circle_material)

# Parameters for the circles
num_circles = 5
circle_radius = 1
circle_offset = 1.5

# Create the circles using the helper function
for i in range(num_circles):
    create_circle(i, circle_radius, circle_offset)


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
