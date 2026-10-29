# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_tablet_using_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of tablet using a Blender script

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the tablet and its screen
mat_tablet = bpy.data.materials.new(name='TabletColor')
mat_tablet.diffuse_color = (0.1, 0.1, 0.1, 1)
mat_display = bpy.data.materials.new(name='DisplayColor')
mat_display.diffuse_color = (0, 0, 0, 1)

# Create a tablet class
class Tablet:
    def __init__(self):
        self.create_tablet_body()
        self.create_screen()

    def create_tablet_body(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        body = bpy.context.object
        body.name = 'TabletBody'
        body.scale = (1, 1.5, 0.05)
        body.data.materials.append(mat_tablet)

    def create_screen(self):
        bpy.ops.mesh.primitive_plane_add(size=1.9, location=(0, 0, 0.051))
        screen = bpy.context.object
        screen.name = 'ScreenPart'
        screen.scale = (0.95, 1.45, 1)
        screen.data.materials.append(mat_display)

# Instantiate the Tablet
Tablet()


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
