# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_code__generate_spice_carousel" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender code, generate spice carousel

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

carousel_material = bpy.data.materials.new(name='Carousel Material')
carousel_material.diffuse_color = (0.6, 0.6, 0.6, 1)
jar_material = bpy.data.materials.new(name='Jar Material')
jar_material.diffuse_color = (1, 1, 1, 1)
lid_material = bpy.data.materials.new(name='Lid Material')
lid_material.diffuse_color = (0.2, 0.2, 0.2, 1)

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

base = create_cylinder(2, 0.2, (0, 0, 0), 'Carousel Base', carousel_material)
handle = create_cylinder(0.1, 2, (0, 0, 1.1), 'Carousel Handle', carousel_material)

for index in range(12):
    theta = index * (2 * math.pi / 12)
    x_pos = 1.5 * math.cos(theta)
    y_pos = 1.5 * math.sin(theta)
    
    jar_body = create_cylinder(0.2, 0.6, (x_pos, y_pos, 0.4), f'Jar {index + 1}', jar_material)
    lid = create_cylinder(0.22, 0.1, (x_pos, y_pos, 0.75), f'Lid {index + 1}', lid_material)
    shaker_top = create_cylinder(0.18, 0.05, (x_pos, y_pos, 0.8), f'Shaker Top {index + 1}', lid_material)


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
