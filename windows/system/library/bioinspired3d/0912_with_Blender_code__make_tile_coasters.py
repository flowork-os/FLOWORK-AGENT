# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_Blender_code__make_tile_coasters" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with Blender code, make tile coasters.

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the coasters
coaster_color_material = bpy.data.materials.new(name='CoasterColor')
coaster_color_material.diffuse_color = (0.8, 0.8, 0.8, 1)  # Light gray

# Function to add a coaster at a given coordinate
def add_coaster(idx, position):
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=1.5, depth=0.1, location=position)
    coaster_item = bpy.context.object
    coaster_item.name = f'Coaster_{idx + 1}'
    coaster_item.data.materials.append(coaster_color_material)

# Loop to create coasters
for index in range(4):
    x_coord = 4 * (index % 2) - 2
    y_coord = 4 * (index // 2) - 2
    add_coaster(index, (x_coord, y_coord, 0))


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
