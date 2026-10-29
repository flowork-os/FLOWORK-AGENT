# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_python_blender_code_that_makes_abstract_sculpture" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate python blender code that makes abstract sculpture

import bpy
import math

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a gray material for the sculpture
mat_gray = bpy.data.materials.new(name="Sculpture Material")
mat_gray.diffuse_color = (0.4, 0.4, 0.4, 1)  # Dark gray color

# Base creation
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.2, location=(0, 0, 0.1))
base_mesh = bpy.context.object
base_mesh.name = "Base"
base_mesh.data.materials.append(mat_gray)

# Flowing shapes parameters
shape_params = [
    ((0, 0, 1), 0.5, (0, 0, math.pi/4)),
    ((0, 0, 2), 0.4, (0, math.pi/4, 0)),
    ((0, 0, 3), 0.3, (math.pi/4, 0, 0)),
    ((0, 0, 4), 0.2, (0, 0, 0))
]

for loc, major_rad, rot in shape_params:
    bpy.ops.mesh.primitive_torus_add(align='WORLD', location=loc, major_radius=major_rad, minor_radius=0.1, rotation=rot)
    shape = bpy.context.object
    shape.name = f"Shape {shape_params.index((loc, major_rad, rot)) + 1}"
    shape.data.materials.append(mat_gray)

# Connecting rods creation
for z in range(1, 4):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(0, 0, 1.5 + z))
    rod_mesh = bpy.context.object
    rod_mesh.name = f"Rod {z}"
    rod_mesh.data.materials.append(mat_gray)


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
