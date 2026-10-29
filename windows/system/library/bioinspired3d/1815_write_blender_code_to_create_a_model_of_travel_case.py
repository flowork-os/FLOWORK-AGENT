# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_code_to_create_a_model_of_travel_case" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender code to create a model of travel case.

import bpy

# Clear all mesh objects before creating new ones
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the objects
mat_circle = bpy.data.materials.new(name='GrayCircle')
mat_circle.diffuse_color = (0.8, 0.8, 0.8, 1)
mat_line = bpy.data.materials.new(name='GrayLine')
mat_line.diffuse_color = (0.2, 0.2, 0.2, 1)

# Class to handle shape creation
class ShapeCreator:
    @staticmethod
    def create_circle(x, y):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.5, minor_radius=0.05, location=(x, y, 0))
        circle = bpy.context.object
        circle.name = f'Circle_{x}_{y}'
        circle.data.materials.append(mat_circle)

    @staticmethod
    def create_line(x, y):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.5, location=(x, y, 0), rotation=(1.5708, 0, 0))
        line = bpy.context.object
        line.name = f'Line_{x}_{y}'
        line.data.materials.append(mat_line)
        line.location = (x + 0.5, y + 0.5, 0)

# Generate the grid of circles and lines
for x in range(5):
    for y in range(5):
        ShapeCreator.create_circle(x, y)
        ShapeCreator.create_line(x, y)


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
