# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_python_code_construct_coffee_maker" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender python code construct coffee maker.

import bpy
import math

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for each part
colors = {
    'body': (0.2, 0.2, 0.2, 1),
    'spout': (0.2, 0.2, 0.2, 1),
    'handle': (0.2, 0.2, 0.2, 1),
    'lid': (0.2, 0.2, 0.2, 1)
}

for name, color in colors.items():
    mat = bpy.data.materials.new(name=f"{name.capitalize()}Material")
    mat.diffuse_color = color

# Create body shape
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 1))
body = bpy.context.object
body.name = "Body"
body.data.materials.append(mat)

# Create spout
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=(1.1, 0, 1.5), rotation=(0, math.pi/4, 0))
spout = bpy.context.object
spout.name = "Spout"
spout.data.materials.append(mat)

# Create handle
bpy.ops.mesh.primitive_torus_add(major_radius=0.5, minor_radius=0.1, location=(-1.5, 0, 1.5), rotation=(math.pi/2, 0, 0))
handle = bpy.context.object
handle.name = "Handle"
handle.data.materials.append(mat)

# Create lid
bpy.ops.mesh.primitive_cylinder_add(radius=1.1, depth=0.1, location=(0, 0, 2.05))
lid = bpy.context.object
lid.name = "Lid"
lid.data.materials.append(mat)


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
