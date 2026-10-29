# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_python_blender_code_that_creates_a_model_of_floral_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate python blender code that creates a model of floral pattern.

import bpy
import math

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the flower petals and center
petal_material = bpy.data.materials.new(name='Pink Petal')
petal_material.diffuse_color = (1, 0.5, 0.5, 1)

center_material = bpy.data.materials.new(name='Yellow Center')
center_material.diffuse_color = (1, 1, 0, 1)

# Functional approach to create a flower
def flower_at(position):
    petal_positions = [(0.2 * math.cos(i * (2 * math.pi / 5)), 0.2 * math.sin(i * (2 * math.pi / 5))) for i in range(5)]
    for x_offset, y_offset in petal_positions:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(position[0] + x_offset, position[1] + y_offset, position[2]))
        bpy.context.object.data.materials.append(petal_material)
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=position)
    bpy.context.object.data.materials.append(center_material)

# Create a grid of flowers
for row in range(5):
    for col in range(5):
        flower_at((row, col, 0))


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
