# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_python_code__make_a_model_of_star_icon" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender python code, make a model of star icon.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_star(points, outer_rad, inner_rad):
    angle_step = math.pi / points
    vertices = []
    for i in range(points * 2):
        radius = outer_rad if i % 2 == 0 else inner_rad
        theta = i * angle_step
        x = radius * math.cos(theta)
        y = radius * math.sin(theta)
        vertices.append((x, y, 0))
    return vertices

num_points = 5
outer_radius = 1.0
inner_radius = 0.4
star_vertices = create_star(num_points, outer_radius, inner_radius)

star_mesh = bpy.data.meshes.new(name="Star")
star_object = bpy.data.objects.new("Star", star_mesh)

bpy.context.collection.objects.link(star_object)

faces = [[i for i in range(num_points * 2)]]

star_mesh.from_pydata(star_vertices, [], faces)
star_mesh.update()

star_material = bpy.data.materials.new(name="StarMaterial")
star_material.diffuse_color = (1, 1, 0, 1)  # Bright yellow
star_object.data.materials.append(star_material)


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
