# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_blender_code__make_bird_cage" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a blender code, make bird cage.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_gray = bpy.data.materials.new(name="Gray Material")
material_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

def create_cylinder(radius, depth, loc):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc)
    return bpy.context.object

cage = create_cylinder(1, 4, (0, 0, 2))
cage.name = "Main Cage"
cage.data.materials.append(material_gray)

bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 4))
dome = bpy.context.object
bpy.ops.transform.resize(value=(1, 1, 0.5))
dome.name = "Dome Top"
dome.data.materials.append(material_gray)

bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1, 0, 2))
door = bpy.context.object
door.name = "Side Door"
door.data.materials.append(material_gray)

perch = create_cylinder(0.05, 2, (0, 0, 1.5))
perch.name = "Perch Bar"
perch.rotation_euler = (0, math.pi/2, 0)
perch.data.materials.append(material_gray)

tray = create_cylinder(1.1, 0.1, (0, 0, 0.05))
tray.name = "Bottom Tray"
tray.data.materials.append(material_gray)


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
