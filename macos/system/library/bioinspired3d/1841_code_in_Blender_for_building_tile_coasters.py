# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_for_building_tile_coasters" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender for building tile coasters

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define material for the coasters
material_for_coasters = bpy.data.materials.new(name='GrayCoaster')
material_for_coasters.diffuse_color = (0.8, 0.8, 0.8, 1)  # Soft gray

# Class to handle coaster creation
class Coaster:
    def __init__(self, index, position):
        self.index = index
        self.position = position
        self.create_coaster()

    def create_coaster(self):
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=1.5, depth=0.1, location=self.position)
        coaster_object = bpy.context.object
        coaster_object.name = f'Coaster_{self.index + 1}'
        coaster_object.data.materials.append(material_for_coasters)

# Create coasters in a grid pattern
for i in range(4):
    x_pos = 4 * (i % 2) - 2
    y_pos = 4 * (i // 2) - 2
    Coaster(i, (x_pos, y_pos, 0))


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
