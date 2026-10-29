# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_Blender_code_that_makes_a_model_of_geometric_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write Blender code that makes a model of geometric pattern.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

new_circle_material = bpy.data.materials.new(name="New Circle Material")
new_circle_material.diffuse_color = (0.4, 0.4, 0.4, 1)  # Dark gray color

def generate_circle(index, radius, distance):
    angle = index * (2 * math.pi / 5)
    x_pos = distance * math.cos(angle)
    y_pos = distance * math.sin(angle)
    bpy.ops.mesh.primitive_torus_add(location=(x_pos, y_pos, 0), major_radius=radius, minor_radius=0.1)
    circle_object = bpy.context.object
    circle_object.name = f"Circle_{index + 1}"
    circle_object.data.materials.append(new_circle_material)

circle_count = 5
circle_radius = 1
circle_distance = 1.5

for j in range(circle_count):
    generate_circle(j, circle_radius, circle_distance)


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
