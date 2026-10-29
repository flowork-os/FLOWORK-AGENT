# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_script_construct_a_model_of_bird_cage" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender script construct a model of bird cage

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_cage = bpy.data.materials.new(name="Steel")
material_cage.diffuse_color = (0.4, 0.4, 0.4, 1)  # Darker gray

class Cage:
    def __init__(self):
        self.base = self.create_cylinder(1, 0.1, (0, 0, 0), "Cage_Base")
        self.top = self.create_cylinder(1, 0.1, (0, 0, 2), "Cage_Top")
        self.create_bars(16)
        self.door = self.create_door()
        self.perch = self.create_perch()

    def create_cylinder(self, radius, depth, location, name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        obj = bpy.context.object
        obj.name = name
        obj.data.materials.append(material_cage)

    def create_bars(self, count):
        for i in range(count):
            theta = (2 * math.pi / count) * i
            x = math.cos(theta)
            y = math.sin(theta)
            self.create_cylinder(0.05, 2, (x, y, 1), f"Cage_Bar_{i + 1}")

    def create_door(self):
        bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1, 0, 1))
        door = bpy.context.object
        door.name = "Cage_Door"
        door.data.materials.append(material_cage)

    def create_perch(self):
        self.create_cylinder(0.05, 1.5, (0, 0, 0.5), "Cage_Perch")

Cage()


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
