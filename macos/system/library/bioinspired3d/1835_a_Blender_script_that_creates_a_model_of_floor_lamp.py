# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_creates_a_model_of_floor_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that creates a model of floor lamp

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

metallic_surface = bpy.data.materials.new(name="Metal Surface")
metallic_surface.diffuse_color = (0.5, 0.5, 0.5, 1)
white_surface = bpy.data.materials.new(name="White Surface")
white_surface.diffuse_color = (1, 1, 1, 1)

class Lamp:
    def __init__(self):
        self.create_stand()
        self.create_base()
        self.create_lampshade()

    def create_stand(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(0, 0, 1))
        stand = bpy.context.object
        stand.name = "Lamp Stand"
        stand.data.materials.append(metallic_surface)

    def create_base(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(0, 0, 0.05))
        base = bpy.context.object
        base.name = "Lamp Base"
        base.data.materials.append(metallic_surface)

    def create_lampshade(self):
        bpy.ops.mesh.primitive_cone_add(radius1=0.4, radius2=0.1, depth=0.6, location=(0, 0, 2.3))
        lampshade = bpy.context.object
        lampshade.name = "Lamp Shade"
        lampshade.data.materials.append(white_surface)

Lamp()


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
