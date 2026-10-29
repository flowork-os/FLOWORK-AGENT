# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_builds_electric_kettle" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that builds electric kettle.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

kettle_material = bpy.data.materials.new(name='Kettle Material')
kettle_material.diffuse_color = (0.6, 0.6, 0.6, 1)  # Lighter gray
base_material = bpy.data.materials.new(name='Base Material')
base_material.diffuse_color = (0.2, 0.2, 0.2, 1)  # Darker gray

class Kettle:
    def __init__(self):
        self.body = self.create_body()
        self.spout = self.create_spout()
        self.handle = self.create_handle()
        self.base = self.create_base()

    def create_body(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 1))
        body = bpy.context.object
        body.name = 'Kettle Body'
        body.data.materials.append(kettle_material)
        return body

    def create_spout(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=(1.1, 0, 1.5), rotation=(0, math.pi / 4, 0))
        spout = bpy.context.object
        spout.name = 'Spout'
        spout.data.materials.append(kettle_material)
        return spout

    def create_handle(self):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.1, location=(-1.5, 0, 1.5), rotation=(math.pi / 2, 0, 0))
        handle = bpy.context.object
        handle.name = 'Handle'
        handle.data.materials.append(kettle_material)
        return handle

    def create_base(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=1.2, depth=0.2, location=(0, 0, 0.1))
        base = bpy.context.object
        base.name = 'Base'
        base.data.materials.append(base_material)
        return base

kettle = Kettle()


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
