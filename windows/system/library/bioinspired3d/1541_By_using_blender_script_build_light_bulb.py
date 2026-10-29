# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_script_build_light_bulb" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender script build light bulb.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_for_bulb = bpy.data.materials.new(name="Bulb Material")
material_for_bulb.diffuse_color = (1, 1, 1, 1)  # Bright white
material_for_base = bpy.data.materials.new(name="Base Material")
material_for_base.diffuse_color = (0.2, 0.2, 0.2, 1)  # Dark gray

class LampCreator:
    @staticmethod
    def create_bulb():
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 1))
        bulb = bpy.context.object
        bulb.name = "Lamp Bulb"
        bulb.data.materials.append(material_for_bulb)

    @staticmethod
    def create_base():
        bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.6, location=(0, 0, 0.3))
        base = bpy.context.object
        base.name = "Lamp Base"
        base.data.materials.append(material_for_base)

    @staticmethod
    def create_ridges():
        for i in range(4):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.35, minor_radius=0.02, location=(0, 0, 0.3 + (i * 0.1)))
            ridge = bpy.context.object
            ridge.name = f"Ridge {i + 1}"
            ridge.data.materials.append(material_for_base)

LampCreator.create_bulb()
LampCreator.create_base()
LampCreator.create_ridges()


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
