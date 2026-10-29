# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_python_blender_code_that_creates_travel_case" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate python blender code that creates travel case

import bpy

# Remove all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Set up materials
material_circle = bpy.data.materials.new('CircleMaterial')
material_circle.diffuse_color = (0.8, 0.8, 0.8, 1)
material_line = bpy.data.materials.new('LineMaterial')
material_line.diffuse_color = (0.2, 0.2, 0.2, 1)

# Generate geometry
for x in range(5):
    for y in range(5):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.5, minor_radius=0.05, location=(x, y, 0))
        current_circle = bpy.context.object
        current_circle.name = f'Circle_{x}_{y}'
        current_circle.data.materials.append(material_circle)

        bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.5, location=(x, y, 0), rotation=(1.5708, 0, 0))
        current_line = bpy.context.object
        current_line.name = f'Line_{x}_{y}'
        current_line.data.materials.append(material_line)
        current_line.location = (x + 0.5, y + 0.5, 0)


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
