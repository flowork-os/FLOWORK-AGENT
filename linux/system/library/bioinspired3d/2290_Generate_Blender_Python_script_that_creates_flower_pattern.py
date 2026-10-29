# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_Python_script_that_creates_flower_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender Python script that creates flower pattern

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

red_petal = bpy.data.materials.new(name="Red Petal")
red_petal.diffuse_color = (1, 0, 0, 1)
yellow_center = bpy.data.materials.new(name="Yellow Center")
yellow_center.diffuse_color = (1, 1, 0, 1)

class Flower:
    def __init__(self, position):
        self.position = position
        self.create_flower()

    def create_flower(self):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=self.position)
        center_obj = bpy.context.object
        center_obj.name = "Flower Center"
        center_obj.data.materials.append(yellow_center)
        
        for i in range(5):
            angle = i * (2 * math.pi / 5)
            x = self.position[0] + 0.3 * math.cos(angle)
            y = self.position[1] + 0.3 * math.sin(angle)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(x, y, self.position[2]))
            petal_obj = bpy.context.object
            petal_obj.name = f"Petal {i + 1}"
            petal_obj.data.materials.append(red_petal)

locations = [(0, 0, 0), (1, 1, 0), (-1, -1, 0), (1, -1, 0), (-1, 1, 0)]
for loc in locations:
    Flower(loc)


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
